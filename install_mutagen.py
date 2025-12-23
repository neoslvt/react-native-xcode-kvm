#!/usr/bin/env python3
"""
Install mutagen for Linux systems.
Supports multiple package managers: apt, yum, dnf, pacman, brew
"""

import subprocess
import sys
import shutil
import os
import platform
from pathlib import Path


def run_command(cmd, check=True, shell=False):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd if (shell or not isinstance(cmd, str)) else cmd.split(),
            check=check,
            capture_output=True,
            text=True,
            shell=shell
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_mutagen_installed():
    """Check if mutagen is already installed."""
    return shutil.which("mutagen") is not None


def install_via_package_manager():
    """Try to install mutagen via system package manager."""
    # Check which package manager is available
    package_managers = {
        'apt': ['sudo', 'apt-get', 'update', '-y'],
        'yum': None,  # CentOS/RHEL usually doesn't have mutagen in repos
        'dnf': None,
        'pacman': ['sudo', 'pacman', '-S', '--noconfirm', 'mutagen'],
        'brew': ['brew', 'install', 'mutagen-io/mutagen/mutagen']
    }
    
    install_commands = {
        'apt': ['sudo', 'apt-get', 'install', '-y', 'mutagen'],
        'yum': None,
        'dnf': None,
        'pacman': ['sudo', 'pacman', '-S', '--noconfirm', 'mutagen'],
        'brew': ['brew', 'install', 'mutagen-io/mutagen/mutagen']
    }
    
    for pm, update_cmd in package_managers.items():
        if shutil.which(pm):
            print(f"Found {pm} package manager")
            if update_cmd:
                print(f"Updating package list...")
                success, stdout, stderr = run_command(update_cmd)
                if not success:
                    print(f"Warning: Failed to update package list: {stderr}")
            
            install_cmd = install_commands[pm]
            if install_cmd:
                print(f"Installing mutagen via {pm}...")
                success, stdout, stderr = run_command(install_cmd)
                if success:
                    print("✓ Mutagen installed successfully!")
                    return True
                else:
                    print(f"Failed to install via {pm}: {stderr}")
    
    return False


def install_via_github_release():
    """Install mutagen from GitHub releases."""
    print("Attempting to install mutagen from GitHub releases...")
    
    # Detect architecture
    machine = platform.machine().lower()
    system = platform.system().lower()
    
    arch_map = {
        'x86_64': 'amd64',
        'amd64': 'amd64',
        'aarch64': 'arm64',
        'arm64': 'arm64',
        'armv7l': 'arm',
    }
    
    if system != 'linux':
        print(f"Error: This script is designed for Linux, detected: {system}")
        return False
    
    arch = arch_map.get(machine, 'amd64')
    print(f"Detected architecture: {arch}")
    
    # Download mutagen
    version = "0.17.3"  # Latest stable version
    url = f"https://github.com/mutagen-io/mutagen/releases/download/v{version}/mutagen_linux_{arch}_v{version}.tar.gz"
    
    download_path = Path("/tmp/mutagen.tar.gz")
    extract_path = Path("/tmp/mutagen_extract")
    
    # Download
    print(f"Downloading mutagen v{version}...")
    success, stdout, stderr = run_command(
        f"curl -L -o {download_path} {url}",
        shell=True
    )
    if not success:
        print(f"Failed to download mutagen: {stderr}")
        return False
    
    # Extract
    print("Extracting...")
    extract_path.mkdir(exist_ok=True)
    success, stdout, stderr = run_command(
        f"tar -xzf {download_path} -C {extract_path}",
        shell=True
    )
    if not success:
        print(f"Failed to extract: {stderr}")
        return False
    
    # Install binary
    mutagen_binary = extract_path / "mutagen"
    if not mutagen_binary.exists():
        print("Error: mutagen binary not found in extracted archive")
        return False
    
    # Copy to /usr/local/bin (requires sudo)
    print("Installing mutagen binary to /usr/local/bin...")
    success, stdout, stderr = run_command(
        f"sudo cp {mutagen_binary} /usr/local/bin/mutagen",
        shell=True
    )
    if not success:
        print(f"Failed to install binary: {stderr}")
        return False
    
    # Make executable
    success, stdout, stderr = run_command(
        "sudo chmod +x /usr/local/bin/mutagen",
        shell=True
    )
    
    # Cleanup
    download_path.unlink(missing_ok=True)
    shutil.rmtree(extract_path, ignore_errors=True)
    
    print("✓ Mutagen installed successfully from GitHub release!")
    return True


def main():
    """Main installation function."""
    print("=" * 50)
    print("Mutagen Installation Script")
    print("=" * 50)
    
    # Check if already installed
    if check_mutagen_installed():
        print("✓ Mutagen is already installed!")
        success, stdout, stderr = run_command("mutagen version")
        if success:
            print(stdout)
        sys.exit(0)
    
    # Try package manager first
    print("\n1. Trying package manager installation...")
    if install_via_package_manager():
        sys.exit(0)
    
    # Fall back to GitHub release
    print("\n2. Trying GitHub release installation...")
    if install_via_github_release():
        sys.exit(0)
    
    print("\n✗ Failed to install mutagen. Please install manually:")
    print("  Visit: https://mutagen.io/documentation/introduction/installation")
    sys.exit(1)


if __name__ == "__main__":
    main()

