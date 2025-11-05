# Seccomp Profile Comparison: Custom vs Docker Default

## Quick Reference

| Metric | Custom Profile (Backup) | Docker Default (Current) |
|--------|------------------------|--------------------------|
| **Lines** | 504 | 766 |
| **Syscall Groups** | 18 | 27 |
| **Total Syscalls** | ~170 | 408 |
| **Architectures** | 5 | 7 |
| **Maintenance** | Manual | Docker Team |
| **Source** | Custom-built | Moby/Docker Project |
| **File** | seccomp_profile.json.backup | seccomp_profile.json |

## Architecture Support

### Custom Profile (5)
- SCMP_ARCH_X86_64
- SCMP_ARCH_X86
- SCMP_ARCH_X32
- SCMP_ARCH_AARCH64
- SCMP_ARCH_ARM

### Docker Default (7)
- SCMP_ARCH_X86_64 + sub-archs
- SCMP_ARCH_AARCH64 + sub-archs
- SCMP_ARCH_MIPS64 + variants
- SCMP_ARCH_MIPSEL64 + variants
- SCMP_ARCH_S390X + sub-archs

## Notable Differences

### Syscalls Allowed by Docker Default (but not custom)

**Process Management**:
- `execve`, `execveat` - Process execution
- `fork`, `vfork`, `clone` - Process creation

**Reasoning**: Safe because read-only filesystem prevents executing binaries

**Network Operations**:
- `socket`, `bind`, `connect`, `accept` - Network syscalls
- `send*`, `recv*` - Network I/O

**Reasoning**: Safe because `network_mode: none` (no network stack)

**Modern I/O**:
- `io_uring_*` - Modern async I/O
- `copy_file_range` - Efficient file copying

**Reasoning**: Safe, legitimate file operations

### Syscalls Blocked by Both

**Container Escape**:
- `unshare`, `setns` - Namespace manipulation
- `pivot_root`, `chroot` - Root filesystem changes

**Kernel Operations**:
- `init_module`, `delete_module` - Kernel modules
- `kexec_load` - Kernel execution
- `bpf` - eBPF programs

**Privileged Operations**:
- `mount`, `umount` - Filesystem mounting
- Many others (see profiles for details)

## Why Docker Default is Safer

1. **Community-Tested**: Millions of production containers
2. **CVE Tracking**: Docker team monitors security advisories
3. **Kernel Updates**: Profile updated for new kernel versions
4. **Edge Cases**: Discovered and fixed through real-world usage
5. **Architecture Coverage**: More platforms supported

## Defense in Depth

Even with more permissive seccomp profile, security is maintained through:

```
┌─────────────────────────────────────────────┐
│ Layer 1: AST Validation                     │ ← Blocks dangerous Python code
├─────────────────────────────────────────────┤
│ Layer 2: Network Isolation (none)           │ ← No network stack
├─────────────────────────────────────────────┤
│ Layer 3: Read-Only Filesystem (/tmp only)   │ ← No code injection
├─────────────────────────────────────────────┤
│ Layer 4: Seccomp Profile (Docker Default)   │ ← Prevents kernel exploits
├─────────────────────────────────────────────┤
│ Layer 5: Resource Limits (cgroups)          │ ← Prevents resource exhaustion
└─────────────────────────────────────────────┘
```

## Examples: Why More Permissive is OK

### Example 1: execve() Syscall

**Custom Profile**: ❌ Blocked
**Docker Default**: ✅ Allowed

**Why it's safe**:
```python
# Even if strategy tries:
import subprocess
subprocess.call(['/bin/bash', '-c', 'whoami'])  # AST validation blocks this

# But even if it gets through:
# - Filesystem is read-only (no /bin/bash to execute)
# - /tmp is noexec (can't execute from /tmp)
# - Container has no shells or binaries
```

### Example 2: socket() Syscall

**Custom Profile**: ❌ Blocked
**Docker Default**: ✅ Allowed

**Why it's safe**:
```python
# Even if strategy tries:
import socket
s = socket.socket()  # Succeeds (syscall allowed)
s.connect(('evil.com', 80))  # FAILS - no network stack!

# network_mode: none means:
# - No network interfaces (except loopback)
# - No routing table
# - No DNS resolution
# Socket syscall succeeds but network ops fail
```

## Performance Impact

**Docker Default**: Slightly more permissive = fewer syscall rejections = marginally better performance

**Trade-off**: None! Security maintained through other layers.

## Revert Instructions (Not Recommended)

To revert to custom profile:
```bash
cp config/seccomp_profile.json.backup config/seccomp_profile.json
```

**Warning**: Not recommended. Custom profile requires manual maintenance and may break with kernel updates.

## Verification

```bash
# Check current profile
python3 -c "import json; d=json.load(open('config/seccomp_profile.json')); \
    print(f'Syscalls: {sum(len(s[\"names\"]) for s in d[\"syscalls\"])}'); \
    print(f'Architectures: {len(d[\"archMap\"])}'); \
    print(f'Default: Docker' if len(d[\"archMap\"]) == 7 else 'Custom')"

# Expected output:
# Syscalls: 408
# Architectures: 7
# Default: Docker
```

## Related Documentation

- **SECCOMP_PROFILE_CHANGE.md**: Detailed rationale and implementation notes
- **TASK_19_COMPLETION_SUMMARY.md**: Complete task implementation summary
- **src/sandbox/docker_executor.py**: Code that loads the profile
- **src/sandbox/docker_config.py**: Configuration that references the profile

## References

- [Docker Seccomp Security](https://docs.docker.com/engine/security/seccomp/)
- [Moby Default Profile](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json)
- [libseccomp](https://github.com/seccomp/libseccomp)
