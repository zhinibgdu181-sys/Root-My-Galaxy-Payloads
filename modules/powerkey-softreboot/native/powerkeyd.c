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
#define MAX_POWER_DEVS 32
#define DUPLICATE_GUARD_MS 120
#define BITS_PER_LONG (sizeof(unsigned long) * 8)
#define NBITS(x) ((((x) - 1) / BITS_PER_LONG) + 1)

static const char *g_log = "/data/adb/modules/powerkey_ksu_softreboot/power-soft-reboot.log";
static volatile sig_atomic_t g_stop = 0;

struct power_dev {
    int fd;
    char path[256];
    char name[128];
};

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

static bool supports_power_key(int fd) {
    unsigned long ev_bits[NBITS(EV_MAX + 1)];
    memset(ev_bits, 0, sizeof(ev_bits));
    if (ioctl(fd, EVIOCGBIT(0, sizeof(ev_bits)), ev_bits) < 0 ||
        !test_bit(EV_KEY, ev_bits)) {
        return false;
    }

    unsigned long key_bits[NBITS(KEY_MAX + 1)];
    memset(key_bits, 0, sizeof(key_bits));
    return ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(key_bits)), key_bits) >= 0 &&
           test_bit(KEY_POWER, key_bits);
}

static int collect_power_devices(struct power_dev *devs, int max_devs) {
    DIR *dir = opendir("/dev/input");
    if (!dir) return -1;

    int count = 0;
    struct dirent *de;
    while ((de = readdir(dir)) != NULL && count < max_devs) {
        if (strncmp(de->d_name, "event", 5) != 0) continue;

        char path[256];
        snprintf(path, sizeof(path), "/dev/input/%s", de->d_name);
        int fd = open(path, O_RDONLY | O_CLOEXEC | O_NONBLOCK);
        if (fd < 0) continue;

        if (!supports_power_key(fd)) {
            close(fd);
            continue;
        }

        devs[count].fd = fd;
        snprintf(devs[count].path, sizeof(devs[count].path), "%s", path);
        memset(devs[count].name, 0, sizeof(devs[count].name));
        if (ioctl(fd, EVIOCGNAME(sizeof(devs[count].name)), devs[count].name) < 0) {
            snprintf(devs[count].name, sizeof(devs[count].name), "unknown");
        }
        ++count;
    }

    closedir(dir);
    return count;
}

static const char *find_ksud(void) {
    static const char *paths[] = {
        "/data/local/tmp/ksud-s25u-kdp",
        "/data/adb/ksud",
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

    char msg[384];
    snprintf(msg, sizeof(msg), "TRIGGER: %s soft-reboot", ksud);
    log_line(msg);
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
    signal(SIGCHLD, SIG_IGN);

    int lockfd = open("/data/adb/modules/powerkey_ksu_softreboot/powerkeyd.lock",
                      O_CREAT | O_RDWR | O_CLOEXEC, 0600);
    if (lockfd < 0) return 2;

    if (flock(lockfd, LOCK_EX | LOCK_NB) != 0) {
        log_line("INFO: another powerkeyd instance is already running; exit");
        return 0;
    }

    ftruncate(lockfd, 0);
    dprintf(lockfd, "%d\n", getpid());

    struct power_dev devs[MAX_POWER_DEVS];
    memset(devs, 0, sizeof(devs));
    for (int i = 0; i < MAX_POWER_DEVS; ++i) devs[i].fd = -1;

    int ndev = 0;
    for (int attempt = 0; attempt < 30 && !g_stop; ++attempt) {
        ndev = collect_power_devices(devs, MAX_POWER_DEVS);
        if (ndev > 0) break;
        sleep(2);
    }

    if (ndev <= 0) {
        log_line("ERROR: no input device advertising KEY_POWER was found");
        return 3;
    }

    char start_msg[256];
    snprintf(start_msg, sizeof(start_msg),
             "START: native multi-device watcher pid=%d devices=%d press_count=%d window_ms=%d",
             getpid(), ndev, press_count, window_ms);
    log_line(start_msg);

    for (int i = 0; i < ndev; ++i) {
        char msg[512];
        snprintf(msg, sizeof(msg), "DEVICE[%d]: %s name=%s", i, devs[i].path, devs[i].name);
        log_line(msg);
    }

    struct pollfd pfds[MAX_POWER_DEVS];
    for (int i = 0; i < ndev; ++i) {
        pfds[i].fd = devs[i].fd;
        pfds[i].events = POLLIN;
        pfds[i].revents = 0;
    }

    int count = 0;
    long long first_ms = 0;
    long long last_accepted_ms = -1000000;

    while (!g_stop) {
        int pr = poll(pfds, (nfds_t)ndev, -1);
        if (pr < 0) {
            if (errno == EINTR) continue;
            log_line("ERROR: poll failed");
            break;
        }

        for (int i = 0; i < ndev; ++i) {
            if (!(pfds[i].revents & POLLIN)) continue;

            struct input_event ev;
            ssize_t n;
            while ((n = read(devs[i].fd, &ev, sizeof(ev))) == (ssize_t)sizeof(ev)) {
                if (ev.type != EV_KEY || ev.code != KEY_POWER || ev.value != 1) continue;

                long long now = monotonic_ms();

                // A single physical POWER press can be mirrored by more than one
                // input node on some Samsung devices. Count it only once.
                if (now - last_accepted_ms < DUPLICATE_GUARD_MS) {
                    char dup[256];
                    snprintf(dup, sizeof(dup),
                             "POWER_DOWN duplicate ignored device=%s delta_ms=%lld",
                             devs[i].path, now - last_accepted_ms);
                    log_line(dup);
                    continue;
                }
                last_accepted_ms = now;

                if (count == 0 || now - first_ms > window_ms) {
                    count = 1;
                    first_ms = now;
                } else {
                    ++count;
                }

                char msg[320];
                snprintf(msg, sizeof(msg),
                         "POWER_DOWN count=%d elapsed_ms=%lld device=%s name=%s",
                         count, now - first_ms, devs[i].path, devs[i].name);
                log_line(msg);

                if (count >= press_count && now - first_ms <= window_ms) {
                    count = 0;
                    first_ms = 0;
                    trigger_soft_reboot();
                    sleep(1);
                }
            }

            if (n < 0 && errno != EAGAIN && errno != EINTR) {
                char msg[256];
                snprintf(msg, sizeof(msg), "WARN: read failed device=%s errno=%d",
                         devs[i].path, errno);
                log_line(msg);
            }
        }
    }

    for (int i = 0; i < ndev; ++i) {
        if (devs[i].fd >= 0) close(devs[i].fd);
    }

    log_line("STOP: native watcher exited");
    return 0;
}
