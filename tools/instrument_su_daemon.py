#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: instrument_su_daemon.py INPUT OUTPUT")

src = Path(sys.argv[1]).read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global src
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    src = src.replace(old, new, 1)


replace_once(
    "static int verify_kernelsu_control(void) {\n"
    "  int fd = -1;\n"
    "  syscall(SYS_reboot, 0xDEADBEEF, 0xCAFEBABE, 0, &fd);\n"
    "  if (fd < 0) {\n"
    "    dprintf(STDERR_FILENO, \"late-load: KernelSU driver fd unavailable\\n\");\n"
    "    return 13;\n"
    "  }\n",
    "static int verify_kernelsu_control(void) {\n"
    "  dprintf(STDOUT_FILENO,\n"
    "          \"[ksu-native] KSU_CONTROL_PROBE_START pid=%d\\n\", getpid());\n"
    "  int fd = -1;\n"
    "  errno = 0;\n"
    "  syscall(SYS_reboot, 0xDEADBEEF, 0xCAFEBABE, 0, &fd);\n"
    "  int reboot_errno = errno;\n"
    "  if (fd < 0) {\n"
    "    dprintf(STDERR_FILENO,\n"
    "            \"[ksu-native] KSU_CONTROL_FD_UNAVAILABLE errno=%d (%s)\\n\",\n"
    "            reboot_errno, strerror(reboot_errno));\n"
    "    return 13;\n"
    "  }\n"
    "  dprintf(STDOUT_FILENO, \"[ksu-native] KSU_CONTROL_FD_READY fd=%d\\n\", fd);\n",
    "control-probe-entry",
)

replace_once(
    "  struct ksu_get_info_cmd info;\n"
    "  memset(&info, 0, sizeof(info));\n"
    "  int ret = ioctl(fd, _IOR('K', 2, struct ksu_get_info_cmd), &info);\n"
    "  int saved_errno = errno;\n"
    "  close(fd);\n",
    "  struct ksu_get_info_cmd info;\n"
    "  memset(&info, 0, sizeof(info));\n"
    "  errno = 0;\n"
    "  int ret = ioctl(fd, _IOR('K', 2, struct ksu_get_info_cmd), &info);\n"
    "  int saved_errno = errno;\n"
    "  close(fd);\n"
    "  dprintf(STDOUT_FILENO,\n"
    "          \"[ksu-native] KSU_CONTROL_IOCTL ret=%d errno=%d version=%u \"\n"
    "          \"flags=0x%x uapi=%u features=0x%x\\n\",\n"
    "          ret, saved_errno, info.version, info.flags, info.uapi_version,\n"
    "          info.features);\n",
    "control-ioctl",
)

replace_once(
    "          info.version, info.flags, info.uapi_version, info.features);\n"
    "  return 0;\n"
    "}\n\n"
    "static int run_kernelsu_late_load",
    "          info.version, info.flags, info.uapi_version, info.features);\n"
    "  dprintf(STDOUT_FILENO, \"[ksu-native] KSU_CONTROL_VERIFIED\\n\");\n"
    "  return 0;\n"
    "}\n\n"
    "static int run_kernelsu_late_load",
    "control-success",
)

replace_once(
    "    close(conn);\n"
    "    close_request_fds(request);\n\n"
    "    if (unshare(CLONE_NEWNS) != 0 ||\n",
    "    close(conn);\n"
    "    close_request_fds(request);\n\n"
    "    dprintf(STDOUT_FILENO,\n"
    "            \"[ksu-native] KSU_NATIVE_START pid=%d loader=%s bind_target=%s\\n\",\n"
    "            getpid(), KSU_LOADER_PATH, LOGCAT_PATH);\n"
    "    struct stat loader_stat;\n"
    "    if (stat(KSU_LOADER_PATH, &loader_stat) == 0) {\n"
    "      dprintf(STDOUT_FILENO,\n"
    "              \"[ksu-native] KSU_LOADER_FILE_OK size=%lld mode=%o\\n\",\n"
    "              (long long)loader_stat.st_size,\n"
    "              (unsigned int)(loader_stat.st_mode & 07777));\n"
    "    } else {\n"
    "      dprintf(STDERR_FILENO,\n"
    "              \"[ksu-native] KSU_LOADER_FILE_FAIL errno=%d (%s)\\n\", errno,\n"
    "              strerror(errno));\n"
    "    }\n\n"
    "    if (unshare(CLONE_NEWNS) != 0 ||\n",
    "late-load-entry",
)

replace_once(
    "      _exit(10);\n"
    "    }\n"
    "    if (mount(KSU_LOADER_PATH, LOGCAT_PATH, NULL, MS_BIND, NULL) != 0) {\n",
    "      _exit(10);\n"
    "    }\n"
    "    dprintf(STDOUT_FILENO, \"[ksu-native] KSU_NAMESPACE_OK\\n\");\n"
    "    if (mount(KSU_LOADER_PATH, LOGCAT_PATH, NULL, MS_BIND, NULL) != 0) {\n",
    "namespace-ok",
)

replace_once(
    "      _exit(11);\n"
    "    }\n\n"
    "    pid_t loader = fork();\n",
    "      _exit(11);\n"
    "    }\n"
    "    dprintf(STDOUT_FILENO,\n"
    "            \"[ksu-native] KSU_BIND_MOUNT_OK source=%s target=%s\\n\",\n"
    "            KSU_LOADER_PATH, LOGCAT_PATH);\n\n"
    "    pid_t loader = fork();\n",
    "bind-ok",
)

replace_once(
    "    if (loader == 0) {\n"
    "      /* Let the downloaded target-specific ksud select its embedded module\n",
    "    if (loader == 0) {\n"
    "      dprintf(STDOUT_FILENO,\n"
    "              \"[ksu-native] KSU_LOADER_EXEC pid=%d path=%s \"\n"
    "              \"args=late-load,--ephemeral\\n\",\n"
    "              getpid(), LOGCAT_PATH);\n"
    "      /* Let the downloaded target-specific ksud select its embedded module\n",
    "loader-exec",
)

replace_once(
    "      _exit(12);\n"
    "    }\n\n"
    "    int loader_status = wait_status(loader);\n"
    "    if (loader_status != 0) {\n"
    "      _exit(loader_status);\n"
    "    }\n"
    "    _exit(verify_kernelsu_control());\n",
    "      _exit(12);\n"
    "    }\n\n"
    "    dprintf(STDOUT_FILENO,\n"
    "            \"[ksu-native] KSU_LOADER_FORK parent=%d loader=%d\\n\", getpid(),\n"
    "            loader);\n"
    "    int loader_status = wait_status(loader);\n"
    "    if (loader_status >= 128) {\n"
    "      dprintf(STDERR_FILENO,\n"
    "              \"[ksu-native] KSU_LOADER_SIGNAL signal=%d status=%d\\n\",\n"
    "              loader_status - 128, loader_status);\n"
    "    } else {\n"
    "      dprintf(STDOUT_FILENO, \"[ksu-native] KSU_LOADER_EXIT rc=%d\\n\",\n"
    "              loader_status);\n"
    "    }\n"
    "    if (loader_status != 0) {\n"
    "      _exit(loader_status);\n"
    "    }\n"
    "    dprintf(STDOUT_FILENO, \"[ksu-native] KSU_CONTROL_PROBE_DISPATCH\\n\");\n"
    "    _exit(verify_kernelsu_control());\n",
    "loader-result",
)

Path(sys.argv[2]).write_text(src, encoding="utf-8")
