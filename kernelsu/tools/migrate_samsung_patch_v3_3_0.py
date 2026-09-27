#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

def read(rel):
    return (root / rel).read_text()

def write(rel, data):
    (root / rel).write_text(data)

def repl(data, old, new, rel):
    count = data.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected exactly one match, found {count}: {old[:120]!r}")
    return data.replace(old, new, 1)

# kernel/Kbuild
rel = "kernel/Kbuild"
s = read(rel)
s = repl(s,
    "kernelsu-objs := core/init.o\n\n",
    "kernelsu-objs := core/init.o\n\n"
    "kernelsu-objs += compat/samsung_kdp.o\n"
    "kernelsu-objs += compat/samsung_defex.o\n\n",
    rel)
s = repl(s,
    "ifeq ($(CONFIG_KSU_X86_PATCH_SYSCALL_DISPATCHER),y)\n"
    "ccflags-y += -DCONFIG_KSU_X86_PATCH_SYSCALL_DISPATCHER=1\n"
    "endif\n",
    "ifeq ($(CONFIG_KSU_SAMSUNG_KDP),y)\n"
    "ccflags-y += -DCONFIG_KSU_SAMSUNG_KDP=1\n"
    "endif\n"
    "ifeq ($(CONFIG_KSU_SAMSUNG_RKP),y)\n"
    "ccflags-y += -DCONFIG_KSU_SAMSUNG_RKP=1\n"
    "endif\n"
    "ifeq ($(CONFIG_KSU_SAMSUNG_DEFEX),y)\n"
    "ccflags-y += -DCONFIG_KSU_SAMSUNG_DEFEX=1\n"
    "endif\n"
    "ifeq ($(CONFIG_KSU_SAMSUNG_NO_PATCH_TEXT),y)\n"
    "ccflags-y += -DCONFIG_KSU_SAMSUNG_NO_PATCH_TEXT=1\n"
    "endif\n"
    "ifeq ($(CONFIG_KSU_X86_PATCH_SYSCALL_DISPATCHER),y)\n"
    "ccflags-y += -DCONFIG_KSU_X86_PATCH_SYSCALL_DISPATCHER=1\n"
    "endif\n",
    rel)
s = repl(s,
    "ccflags-y += -I$(objtree)/security/selinux -include $(srctree)/include/uapi/asm-generic/errno.h\n",
    "ccflags-y += -I$(objtree)/security/selinux -I$(objtree)/security/selinux/include "
    "-include $(srctree)/include/uapi/asm-generic/errno.h\n",
    rel)
s = repl(s,
    "ccflags-y += -I$(KSU_KERNEL_DIR) -I$(KSU_KERNEL_DIR)/include\n",
    "ccflags-y += -I$(KSU_KERNEL_DIR) -I$(KSU_KERNEL_DIR)/include -I$(KSU_KERNEL_DIR)/..\n",
    rel)
s = repl(s,
    '$(warning "KSU_GIT_VERSION not defined! It is better to make KernelSU a git repository!")\n'
    "ccflags-y += -DKSU_VERSION=16\n",
    '$(warning "KSU_GIT_VERSION not defined! It is better to make KernelSU a git repository!")\n'
    "KSU_VERSION ?= 32601\n"
    "$(info -- KernelSU fallback version: $(KSU_VERSION))\n"
    "ccflags-y += -DKSU_VERSION=$(KSU_VERSION)\n",
    rel)
write(rel, s)

# kernel/core/init.c
rel = "kernel/core/init.c"
s = read(rel)
s = repl(s,
    '#include "policy/allowlist.h"\n',
    '#include "policy/allowlist.h"\n#include "ksu_samsung_kdp.h"\n',
    rel)
s = repl(s,
    '#include "infra/symbol_resolver.h"\n',
    '#include "infra/symbol_resolver.h"\n#include "compat/samsung_defex.h"\n',
    rel)
s = repl(s,
    "int __init kernelsu_init(void)\n{\n",
    "int __init kernelsu_init(void)\n{\n    int ret;\n\n",
    rel)
s = repl(s,
    '    if (allow_shell) {\n'
    '        pr_alert("shell is allowed at init!");\n'
    '    }\n\n'
    '    ksu_cred = prepare_creds();\n'
    '    if (!ksu_cred) {\n'
    '        pr_err("prepare cred failed!\\n");\n'
    '        return -ENOSYS;\n'
    '    }\n\n'
    '    ksu_init_symbol_resolver();\n'
    '    ksu_syscall_hook_init();\n',
    '    if (allow_shell) {\n'
    '        pr_alert("shell is allowed at init!");\n'
    '    }\n\n'
    '#ifdef CONFIG_KSU_SAMSUNG_KDP\n'
    '    pr_info("Samsung KDP credential reference handling enabled\\n");\n'
    '#endif\n\n'
    '    ksu_init_symbol_resolver();\n'
    '    ret = ksu_samsung_kdp_init();\n'
    '    if (ret)\n'
    '        return ret;\n\n'
    '    ksu_cred = prepare_creds();\n'
    '    if (!ksu_cred) {\n'
    '        pr_err("prepare cred failed!\\n");\n'
    '        ksu_samsung_kdp_exit();\n'
    '        return -ENOSYS;\n'
    '    }\n\n'
    '    ret = ksu_samsung_defex_init();\n'
    '    if (ret) {\n'
    '        ksu_put_cred(ksu_cred);\n'
    '        ksu_samsung_kdp_exit();\n'
    '        return ret;\n'
    '    }\n\n'
    '    ksu_syscall_hook_init();\n',
    rel)
s = repl(s,
    "    put_cred(ksu_cred);\n",
    "    ksu_samsung_defex_exit();\n"
    "    ksu_put_cred(ksu_cred);\n"
    "    ksu_samsung_kdp_exit();\n",
    rel)
write(rel, s)

# userspace/ksud/src/late_load.rs
rel = "userspace/ksud/src/late_load.rs"
s = read(rel)
s = repl(s, "use std::process::Command;\n", "", rel)
s = repl(s,
    "pub fn run(package_name: &String, kmi: Option<String>, allow_shell: bool) -> Result<()> {\n"
    "    utils::daemonize(false)?;\n"
    '    info!("late-load command triggered!");\n'
    '    dump_process_info("late-load start");\n\n',
    "pub fn run(_package_name: &String, kmi: Option<String>, allow_shell: bool) -> Result<()> {\n"
    '    info!("late-load command triggered!");\n'
    '    dump_process_info("late-load start");\n\n'
    "    // Stage the daemon before module load changes this process security context.\n"
    '    utils::stage_daemon_from("/data/local/tmp/.ksud-stage").context("Failed to stage ksud")?;\n\n',
    rel)
s = repl(s,
    '    utils::install(None, None).context("Failed to install ksud")?;\n',
    '    utils::finish_install(None, None).context("Failed to finish ksud installation")?;\n',
    rel)
restart = '''    // 14. Restart Manager so it gets a fresh ksu fd from the newly loaded kernel module
    info!("Restarting KernelSU Manager {package_name}...");
    let _ = Command::new("am")
        .args(["force-stop", package_name])
        .status();
    let _ = Command::new("am")
        .args([
            "start",
            "-n",
            &format!("{package_name}/me.weishu.kernelsu.ui.MainActivity"),
        ])
        .status();

'''
s = repl(s, restart, "", rel)
write(rel, s)

# userspace/ksud/src/utils.rs
rel = "userspace/ksud/src/utils.rs"
s = read(rel)
s = repl(s,
    "use rustix::fs::{Mode, OFlags, open};\n",
    "use rustix::fs::{Mode, OFlags, chown, open};\n",
    rel)
s = repl(s,
    "use rustix::stdio::{dup2_stderr, dup2_stdin, dup2_stdout};\n",
    "use rustix::stdio::{dup2_stderr, dup2_stdin, dup2_stdout};\n"
    "use rustix::thread::{Gid, Uid};\n",
    rel)
start = s.index("pub fn install(libadbroot: Option<PathBuf>, data_path: Option<PathBuf>) -> Result<()> {")
end = s.index("\npub fn uninstall(package_name: &str) -> Result<()> {", start)
new_install = r'''pub fn stage_daemon() -> Result<()> {
    ensure_dir_exists(defs::ADB_DIR)?;
    let _ = std::fs::remove_file(defs::DAEMON_PATH);
    std::fs::copy(
        // Preserve upstream v3.3.0 behavior: use /proc/self/exe instead of
        // resolving the executable path before replacing /data/adb/ksud.
        "/proc/self/exe",
        defs::DAEMON_PATH,
    )?;
    #[cfg(unix)]
    set_permissions(defs::DAEMON_PATH, Permissions::from_mode(0o755))?;
    Ok(())
}

pub fn stage_daemon_from(staged_exe: impl AsRef<Path>) -> Result<()> {
    ensure_dir_exists(defs::ADB_DIR)?;
    std::fs::rename(staged_exe.as_ref(), defs::DAEMON_PATH).with_context(|| {
        format!(
            "Failed to rename {} to {}",
            staged_exe.as_ref().display(),
            defs::DAEMON_PATH
        )
    })?;
    chown(defs::DAEMON_PATH, Some(Uid::ROOT), Some(Gid::ROOT))?;
    #[cfg(unix)]
    set_permissions(defs::DAEMON_PATH, Permissions::from_mode(0o755))?;
    Ok(())
}

pub fn finish_install(libadbroot: Option<PathBuf>, data_path: Option<PathBuf>) -> Result<()> {
    restorecon::lsetfilecon(defs::DAEMON_PATH, restorecon::KSU_CON)?;
    assets::ensure_binaries(false).with_context(|| "Failed to extract assets")?;

    link_ksud_to_bin()?;

    if let Some(libadbroot) = libadbroot {
        ensure_dir_exists(defs::LIBRARY_DIR)?;
        let _ = std::fs::remove_file(defs::LIBADBROOT_PATH);
        let _ = std::fs::copy(libadbroot, defs::LIBADBROOT_PATH);
    }

    if let Some(data_path) = data_path {
        let backup_path = data_path.join(KSU_TEMP_BACKUP_DIR_NAME);
        if backup_path.is_dir() {
            for ent in backup_path.read_dir()? {
                let ent = ent?;
                if ent.file_type().is_ok_and(|v| v.is_file()) {
                    let name = ent.file_name().to_string_lossy().to_string();
                    let target = format!("{}{name}", defs::KSU_BACKUP_DIR);
                    if name.starts_with(defs::KSU_BACKUP_FILE_PREFIX)
                        && std::fs::rename(ent.path(), &target).is_err()
                    {
                        std::fs::copy(ent.path(), &target).with_context(|| {
                            format!("failed to move {} -> {target}", ent.path().display())
                        })?;
                        log::info!("move boot backup {name}");
                    }
                }
            }
            std::fs::remove_dir_all(&backup_path)?;
        }
    }

    Ok(())
}

pub fn install(libadbroot: Option<PathBuf>, data_path: Option<PathBuf>) -> Result<()> {
    stage_daemon()?;
    finish_install(libadbroot, data_path)
}
'''
s = s[:start] + new_install + s[end:]
s = repl(s,
    "pub fn daemonize(use_init_pgrp: bool) -> Result<()> {\n"
    "    daemonize_with(use_init_pgrp, || Ok(()))\n"
    "}\n\n",
    "",
    rel)
write(rel, s)

# kernel/hook/arm64/patch_memory.c
rel = "kernel/hook/arm64/patch_memory.c"
s = read(rel)
s = repl(s,
    "int ksu_patch_text(void *dst, void *src, size_t len, int flags)\n{\n"
    "    struct patch_text_info info = {\n",
    "int ksu_patch_text(void *dst, void *src, size_t len, int flags)\n{\n"
    "#ifdef CONFIG_KSU_SAMSUNG_NO_PATCH_TEXT\n"
    '    pr_warn("patch_text disabled for this Samsung target: dst=0x%lx len=%zu flags=0x%x\\n",\n'
    "            (unsigned long)dst, len, flags);\n"
    "    return -EOPNOTSUPP;\n"
    "#else\n"
    "    struct patch_text_info info = {\n",
    rel)
s = repl(s,
    "    return stop_machine(ksu_patch_text_cb, &info, cpu_online_mask);\n"
    "}\n\n"
    "/*\n"
    " * Scan the memory region",
    "    return stop_machine(ksu_patch_text_cb, &info, cpu_online_mask);\n"
    "#endif\n"
    "}\n\n"
    "/*\n"
    " * Scan the memory region",
    rel)
write(rel, s)

# v3.3.0 tag still references the retired Kernel-SU GitHub organization for
# several Rust dependencies. Preserve every pinned revision; only migrate the
# organization URL to the public KernelSU2 mirrors used by later upstream.
for rel in ("userspace/ksud/Cargo.toml", "Cargo.lock"):
    s = read(rel)
    old = "https://github.com/Kernel-SU/"
    new = "https://github.com/KernelSU2/"
    if old not in s:
        raise SystemExit(f"{rel}: retired Kernel-SU dependency URL not found")
    s = s.replace(old, new)
    write(rel, s)

print("v3.3.0 Samsung migration edits applied")
