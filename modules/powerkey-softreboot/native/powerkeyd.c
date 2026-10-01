#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>
#include <dirent.h>

#define DEFAULT_PRESS_COUNT 4
#define DEFAULT_WINDOW_MS 3000
#define BITS_PER_LONG (sizeof(unsigned long) * 8)
#define NBITS(x) ((((x) - 1) / BITS_PER_LONG) + 1)

static const char *g_log = "/data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log";
static volatile sig_atomic_t g_stop = 0;

static void on_signal(int sig) {
    (void)sig;
    g_stop = 1;
}

static long long monotonic_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return (long long)ts.tv_sec * 1000LL + ts.tv_nsec / 1000000LL;
}

static void log_line(const char *msg) {
    FILE *f = fopen(g_log, "a");
    if (!f) return;
    time_t now = time(NULL);
    struct tm tmv;
    localtime_r(&now, &tmv);
    char ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%d %H:%M:%S", &tmv);
    fprintf(f, "%s %s\n", ts, msg);
    fclose(f);
}

static bool test_bit(unsigned int bit, const unsigned long *bits) {
    return (bits[bit / BITS_PER_LONG] >> (bit % BITS_PER_LONG)) & 1UL;
}

static int find_power_device(char *out, size_t out_sz) {
    DIR *dir = opendir("/dev/input");
    if (!dir) return -1;

    struct dirent *de;
    int found = -1;
    while ((de = readdir(dir)) != NULL) {
        if (strncmp(de->d_name, "event", 5) != 0) continue;

        char path[256];
        snprintf(path, sizeof(path), "/dev/input/%s", de->d_name);
        int fd = open(path, O_RDONLY | O_CLOEXEC | O_NONBLOCK);
        if (fd < 0) continue;

        unsigned long ev_bits[NBITS(EV_MAX + 1)];
        memset(ev_bits, 0, sizeof(ev_bits));
        if (ioctl(fd, EVIOCGBIT(0, sizeof(ev_bits)), ev_bits) < 0 ||
            !test_bit(EV_KEY, ev_bits)) {
            close(fd);
            continue;
        }

        unsigned long key_bits[NBITS(KEY_MAX + 1)];
        memset(key_bits, 0, sizeof(key_bits));
        if (ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(key_bits)), key_bits) >= 0 &&
            test_bit(KEY_POWER, key_bits)) {
            snprintf(out, out_sz, "%s", path);
            found = 0;
            close(fd);
            break;
        }
        close(fd);
    }

    closedir(dir);
    return found;
}

static const char *find_ksud(void) {
    static const char *paths[] = {
        "/data/adb/ksud",
        "/data/local/tmp/ksud-s25u-kdp",
        "/system/bin/ksud",
        NULL
    };
    for (int i = 0; paths[i]; ++i) {
        if (access(paths[i], X_OK) == 0) return paths[i];
    }
    return NULL;
}

static void trigger_soft_reboot(void) {
    const char *ksud = find_ksud();
    if (!ksud) {
        log_line("ERROR: ksud executable not found");
        return;
    }

    log_line("TRIGGER: ksud soft-reboot");

    sync();
    pid_t pid = fork();
    if (pid < 0) {
        log_line("ERROR: fork failed");
        return;
    }
    if (pid == 0) {
        int dn = open("/dev/null", O_RDWR | O_CLOEXEC);
        if (dn >= 0) {
            dup2(dn, STDIN_FILENO);
            dup2(dn, STDOUT_FILENO);
            dup2(dn, STDERR_FILENO);
            if (dn > STDERR_FILENO) close(dn);
        }
        execl(ksud, ksud, "soft-reboot", (char *)NULL);
        _exit(127);
    }
}

int main(int argc, char **argv) {
    int press_count = DEFAULT_PRESS_COUNT;
    int window_ms = DEFAULT_WINDOW_MS;
    if (argc >= 2) {
        int v = atoi(argv[1]);
        if (v >= 2 && v <= 10) press_count = v;
    }
    if (argc >= 3) {
        int v = atoi(argv[2]);
        if (v >= 500 && v <= 10000) window_ms = v;
    }

    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);
    signal(SIGHUP, SIG_IGN);

    int lockfd = open("/data/adb/modules/powerkey_ksu_softreboot/powerkeyd.lock",
                      O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (lockfd < 0) return 2;
    if (flock(lockfd, LOCK_EX | LOCK_NB) != 0) {
        log_line("INFO: another powerkeyd instance is already running; exit");
        return 0;
    }
    ftruncate(lockfd, 0);
    dprintf(lockfd, "%d\n", getpid());

    char dev[256] = {0};
    for (int i = 0; i < 30 && !g_stop; ++i) {
        if (find_power_device(dev, sizeof(dev)) == 0) break;
        sleep(2);
    }
    if (!dev[0]) {
        log_line("ERROR: KEY_POWER input device not found");
        return 3;
    }

    int fd = open(dev, O_RDONLY | O_CLOEXEC | O_NONBLOCK);
    if (fd < 0) {
        log_line("ERROR: cannot open KEY_POWER input device");
        return 4;
    }

    char start_msg[384];
    snprintf(start_msg, sizeof(start_msg),
             "START: native poll watcher pid=%d device=%s press_count=%d window_ms=%d",
             getpid(), dev, press_count, window_ms);
    log_line(start_msg);

    int count = 0;
    long long first_ms = 0;

    struct pollfd pfd = {.fd = fd, .events = POLLIN};
    while (!g_stop) {
        int pr = poll(&pfd, 1, -1);
        if (pr < 0) {
            if (errno == EINTR) continue;
            log_line("ERROR: poll failed");
            break;
        }
        if (!(pfd.revents & POLLIN)) continue;

        struct input_event ev;
        ssize_t n;
        while ((n = read(fd, &ev, sizeof(ev))) == (ssize_t)sizeof(ev)) {
            if (ev.type != EV_KEY || ev.code != KEY_POWER || ev.value != 1) continue;

            long long now = monotonic_ms();
            if (count == 0 || now - first_ms > window_ms) {
                count = 1;
                first_ms = now;
            } else {
                ++count;
            }

            char msg[160];
            snprintf(msg, sizeof(msg), "POWER_DOWN count=%d elapsed_ms=%lld",
                     count, now - first_ms);
            log_line(msg);

            if (count >= press_count && now - first_ms <= window_ms) {
                count = 0;
                first_ms = 0;
                trigger_soft_reboot();
                sleep(2);
            }
        }

        if (n < 0 && errno != EAGAIN && errno != EINTR) {
            log_line("ERROR: read failed");
            break;
        }
    }

    close(fd);
    log_line("STOP: native watcher exited");
    return 0;
}
