#!/usr/bin/env python3
"""
Clone OSX-KVM repository and add custom boot script with optimizations.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from getpass import getuser
import multiprocessing


def run_command(cmd, check=True, shell=False, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            check=check,
            capture_output=True,
            text=True,
            shell=shell,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def clone_osx_kvm(target_dir):
    """Clone the OSX-KVM repository."""
    repo_url = "https://github.com/kholia/OSX-KVM.git"
    target_path = Path(target_dir)
    
    if target_path.exists():
        print(f"Directory {target_dir} already exists.")
        response = input("Do you want to update it? (y/n): ").strip().lower()
        if response == 'y':
            print(f"Updating repository in {target_dir}...")
            success, stdout, stderr = run_command(
                "git pull --rebase",
                cwd=target_path
            )
            if success:
                print("✓ Repository updated successfully!")
            else:
                print(f"Warning: Failed to update: {stderr}")
            return target_path
        else:
            print("Skipping clone/update.")
            return target_path
    
    print(f"Cloning OSX-KVM repository to {target_dir}...")
    success, stdout, stderr = run_command(
        f"git clone --depth 1 --recursive {repo_url} {target_dir}",
        shell=True
    )
    
    if not success:
        print(f"Error: Failed to clone repository: {stderr}")
        sys.exit(1)
    
    print("✓ Repository cloned successfully!")
    return target_path


def get_host_resources():
    """
    Detect host CPU cores and RAM, return half for VM allocation.
    Returns: (vm_ram_mb, vm_cores, vm_threads)
    """
    # Get CPU cores (logical cores)
    host_cores = multiprocessing.cpu_count()
    vm_cores = max(1, host_cores // 2)
    vm_threads = vm_cores  # Use same number of threads as cores
    
    # Get total RAM in MB
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    # Format: "MemTotal:       16384128 kB"
                    mem_kb = int(line.split()[1])
                    mem_mb = mem_kb // 1024
                    vm_ram_mb = max(1024, mem_mb // 2)  # Minimum 1GB
                    break
    except (FileNotFoundError, ValueError, IndexError):
        # Fallback if /proc/meminfo not available (shouldn't happen on Linux)
        print("Warning: Could not read /proc/meminfo, using default 6144MB RAM")
        vm_ram_mb = 6144
    
    return vm_ram_mb, vm_cores, vm_threads


def create_custom_boot_script(repo_path, username=None):
    """Create the custom OpenCore boot script with optimizations."""
    if username is None:
        username = getuser()
    
    # Detect host resources and allocate half to VM
    vm_ram_mb, vm_cores, vm_threads = get_host_resources()
    
    print(f"Host resources detected:")
    print(f"  CPU cores: {multiprocessing.cpu_count()}")
    print(f"  Allocating to VM: {vm_cores} cores, {vm_threads} threads, {vm_ram_mb}MB RAM")
    
    repo_path = Path(repo_path)
    script_path = repo_path / "OpenCore-Boot-Custom.sh"
    
    script_content = f"""#!/usr/bin/env bash

# Special thanks to:
# https://github.com/Leoyzen/KVM-Opencore
# https://github.com/thenickdude/KVM-Opencore/
# https://github.com/qemu/qemu/blob/master/docs/usb2.txt
#
# qemu-img create -f qcow2 mac_hdd_ng.img 128G
#
# echo 1 > /sys/module/kvm/parameters/ignore_msrs (this is required)

###############################################################################
# NOTE: Tweak the "MY_OPTIONS" line in case you are having booting problems!
###############################################################################
#
# Change `Penryn` to `Haswell-noTSX` in OpenCore-Boot.sh file for macOS Sonoma!
#
###############################################################################

MY_OPTIONS="+ssse3,+sse4.2,+popcnt,+aes,check"

# Auto-configured: Half of host resources allocated to VM
ALLOCATED_RAM="{vm_ram_mb}"
CPU_SOCKETS="1"
CPU_CORES="{vm_cores}"
CPU_THREADS="{vm_threads}"

REPO_PATH="."
OVMF_DIR="."

args=(
  -enable-kvm
  -machine q35,accel=kvm,usb=off,vmport=off,dump-guest-core=off
  -m "$ALLOCATED_RAM"
  
  # 1. Performance: Hugepages & Memory backing
  -mem-path /dev/hugepages
  -mem-prealloc

  # 2. CPU: Keep 'host' but ensure 'topoext' is there for AMD or proper cache for Intel
  -cpu Haswell-noTSX,kvm=on,vendor=GenuineIntel,+invtsc,+hypervisor,check,"$MY_OPTIONS"
  -smp "$CPU_THREADS",cores="$CPU_CORES",sockets="$CPU_SOCKETS"

  -device isa-applesmc,osk="ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
  -smbios type=2

  -drive if=pflash,format=raw,readonly=on,file="$REPO_PATH/OVMF_CODE.fd"
  -drive if=pflash,format=raw,file="$REPO_PATH/OVMF_VARS-1920x1080.fd"

  # OpenCore
  -drive if=none,id=OpenCore,format=qcow2,snapshot=on,file="$REPO_PATH/OpenCore/OpenCore.qcow2",aio=native,cache=none
  -device nvme,drive=OpenCore,serial=4321,bootindex=0

  # Installer
  -drive if=none,id=InstallMedia,format=raw,file="$REPO_PATH/BaseSystem.img"
  -device virtio-blk-pci,drive=InstallMedia

  # Audio
  -device ich9-intel-hda -device hda-duplex

  # USB
  -device qemu-xhci
  -device usb-kbd
  -device usb-tablet

  # macOS disk
  -drive if=none,id=MacHDD,format=qcow2,file="$REPO_PATH/mac_hdd_ng.img"
  -device nvme,drive=MacHDD,serial=1234

  # 4. Networking: Use vhost for kernel-level speed
  -netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8081-:8081
  -device virtio-net-pci,netdev=net0,mac=52:54:00:c9:18:27

  # Display (IMPORTANT)
  -display gtk,gl=on,show-cursor=on
  #-device ramfb

  -monitor stdio
)

# Setup hugepages ownership
sudo chown {username} /dev/hugepages 2>/dev/null || true

# Execute QEMU
qemu-system-x86_64 "${{args[@]}}"
"""
    
    print(f"Creating custom boot script at {script_path}...")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    print("✓ Custom boot script created and made executable!")
    
    return script_path


def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clone OSX-KVM and add custom boot script"
    )
    parser.add_argument(
        "--target-dir",
        default=os.path.expanduser("~/OSX-KVM"),
        help="Target directory for OSX-KVM repository (default: ~/OSX-KVM)"
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Username for hugepages ownership (default: current user)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("OSX-KVM Setup Script")
    print("=" * 50)
    
    # Clone repository
    repo_path = clone_osx_kvm(args.target_dir)
    
    # Create custom boot script
    script_path = create_custom_boot_script(repo_path, args.username)
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print(f"Repository: {repo_path}")
    print(f"Custom boot script: {script_path}")


if __name__ == "__main__":
    main()

