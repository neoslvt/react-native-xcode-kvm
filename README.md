# React Native macOS KVM Helper Scripts

Complete automation scripts for React Native development on Linux using macOS in a QEMU/KVM virtual machine.

## Features

- 🚀 **One-command installation** - Automated setup of all components
- 🔄 **File synchronization** - Mutagen sync between Linux host and macOS VM
- ⚡ **Quick project setup** - `xcode add` command for instant React Native project configuration
- 🎯 **Auto-configured networking** - Automatic IP detection and Metro bundler configuration
- 📦 **Dependency management** - Automatic npm install in VM
- 🔧 **Optimized VM settings** - Auto-configured CPU and RAM allocation (50% of host resources)

## Quick Start

### 1. Installation

```bash
git clone https://github.com/neoslvt/react-native-xcode-kvm
cd react-native-xcode-kvm
./install.sh
```

This will:
- Install mutagen
- Clone and setup OSX-KVM repository
- Open macOS download in a new terminal tab
- Start macOS installation wizard
- Install the `xcode` command

### 2. Setup React Native Project

```bash
cd /path/to/your/react-native-project
xcode add
```

This will:
- Detect project name and local IP
- Install npm dependencies in the VM
- Create mutagen sync session
- Generate `run_react_native.sh` script

### 3. Run React Native

```bash
xcode run
```

This will SSH into the macOS VM and start Expo with the correct hostname configuration.

## Detailed Documentation

### Installation

The main installation script (`install.sh`) automates the entire setup process:

```bash
./install.sh
```

**What it does:**
1. Installs mutagen (file synchronization tool)
2. Clones OSX-KVM repository to `~/OSX-KVM`
3. Creates optimized boot script with auto-detected resources
4. Opens new terminal tab for macOS download
5. Converts DMG to IMG (if needed)
6. Creates virtual disk (256G default)
7. Starts macOS installation VM
8. Installs `xcode` command to `/bin/xcode`

**Prerequisites:**
- Linux system with QEMU/KVM
- Python 3.6+
- Git
- sudo access
- Terminal emulator (gnome-terminal, konsole, xterm, etc.)

**macOS VM Setup:**
- When installing macOS, **name your user as `macos`** (or update the username in scripts)
- Ensure SSH is enabled
- Install Node.js: `brew install node`

### The `xcode` Command

The `xcode` command provides easy project management.

#### `xcode add`

Sets up a React Native project for macOS VM development:

```bash
cd /path/to/react-native-project
xcode add
```

**What it does:**
- Detects project name from `app.json` or `package.json`
- Detects your Linux host IP address
- Creates mutagen sync session (syncs to `~/src/{project-name}` on VM)
- Installs npm dependencies in the VM
- Generates `run_react_native.sh` script

**Sync configuration:**
- Local path: Your current project directory
- Remote path: `~/src/{project-name}` on macOS VM
- Ignored: `node_modules`, `.expo`, `.git`, build directories

#### `xcode remove`

Removes project setup:

```bash
xcode remove
```

**What it does:**
- Terminates mutagen sync session
- Removes `run_react_native.sh` script

#### `xcode run [args...]`

Runs React Native in the macOS VM:

```bash
# Basic usage (uses --lan mode)
xcode run

# With tunnel
xcode run --tunnel

# With additional Expo flags
xcode run --tunnel --ios
xcode run --clear
```

**What it does:**
- SSH into macOS VM
- Navigate to synced project directory
- Run `run_react_native.sh` with your arguments
- Automatically configures `REACT_NATIVE_PACKAGER_HOSTNAME`

**Arguments:**
- All arguments are passed to `expo start`
- `--lan` is automatically added unless `--tunnel` is specified
- `REACT_NATIVE_PACKAGER_HOSTNAME` is only set when not using `--tunnel`

**Examples:**
```bash
xcode run                    # Expo with LAN mode
xcode run --tunnel           # Expo with tunnel (no LAN, no hostname)
xcode run --tunnel --ios     # Expo tunnel with iOS flag
xcode run --clear            # Expo with cache clear and LAN
```

### Project Setup Flow

1. **Initial Setup** (one time):
   ```bash
   ./install.sh
   ```
   Follow the prompts to download and install macOS.

2. **Per Project Setup**:
   ```bash
   cd your-react-native-project
   xcode add
   ```

3. **Develop**:
   ```bash
   xcode run
   # Or with options:
   xcode run --tunnel
   ```

4. **Cleanup** (when done):
   ```bash
   xcode remove
   ```

### File Synchronization

Mutagen provides real-time bidirectional file synchronization.

**Monitor sync status:**
```bash
mutagen sync list
mutagen sync monitor {project-name}
```

**Sync management:**
```bash
# Pause sync
mutagen sync pause {project-name}

# Resume sync
mutagen sync resume {project-name}

# Terminate sync
mutagen sync terminate {project-name}
```

**Sync details:**
- Files sync in real-time both ways
- `node_modules` is ignored (installed separately in VM)
- Build directories are ignored
- Changes are immediate and efficient

### Networking Configuration

**Host → VM:**
- SSH port forwarding: `localhost:2222` → VM:22
- Default VM user: `macos` (configurable)
- VM IP (user networking): `10.0.2.15`

**VM → Host:**
- Host IP (from VM): `10.0.2.2` (QEMU user network gateway)
- Metro bundler: Automatically configured via `REACT_NATIVE_PACKAGER_HOSTNAME`

**Network Modes:**

1. **LAN Mode** (default):
   - Uses `REACT_NATIVE_PACKAGER_HOSTNAME` environment variable
   - Includes `--lan` flag
   - Best for development on local network

2. **Tunnel Mode** (`--tunnel`):
   - Uses Expo's tunnel service
   - No `REACT_NATIVE_PACKAGER_HOSTNAME` needed
   - No `--lan` flag
   - Works across networks

### VM Resource Allocation

The custom boot script (`OpenCore-Boot-Custom.sh`) automatically:
- Allocates **50% of host CPU cores** to the VM
- Allocates **50% of host RAM** to the VM
- Minimum: 1 CPU core, 1GB RAM

This ensures optimal performance while leaving resources for the host system.

### Troubleshooting

#### npm not found in VM

If you get "command not found: npm":
```bash
# In macOS VM
brew install node
```

#### SSH connection issues

```bash
# Test SSH connection
ssh -p 2222 macos@localhost

# If password prompts are annoying, setup SSH keys:
ssh-copy-id -p 2222 macos@localhost
```

#### Mutagen sync not working

```bash
# Check sync status
mutagen sync list

# Check if SSH works
ssh -p 2222 macos@localhost "echo 'SSH works'"

# Verify remote directory exists
ssh -p 2222 macos@localhost "ls -la ~/src/"
```

#### React Native can't connect to bundler

- Verify `REACT_NATIVE_PACKAGER_HOSTNAME` is set correctly
- Check firewall settings
- Try tunnel mode: `xcode run --tunnel`
- Ensure Metro bundler is running on Linux host

#### Terminal interaction issues

The `xcode run` command uses interactive SSH. If you can't interact:
- Ensure you're using a proper terminal (not a script)
- Check SSH TTY allocation
- Try running directly: `ssh -p 2222 macos@localhost`

#### VM performance issues

- Ensure KVM is enabled: `sudo modprobe kvm`
- Check CPU virtualization support: `egrep -c '(vmx|svm)' /proc/cpuinfo`
- Increase VM resources in `OpenCore-Boot-Custom.sh` if needed

### Configuration

**Default values** (in `xcode` script):
```bash
MACOS_USER="macos"      # macOS VM username
MACOS_PORT=2222         # SSH port
SYNC_SCRIPT="run_react_native.sh"
```

**Change defaults:**
Edit the `xcode` script directly, or set environment variables before running commands.

### Advanced Usage

#### Custom sync path

Edit the `xcode` script or modify the mutagen sync command:
```bash
mutagen sync create \
    --name="my-app" \
    /local/path \
    macos@localhost:2222:~/custom/path \
    --ignore="node_modules" \
    --ignore=".expo" \
    --ignore=".git"
```

#### Manual VM boot

```bash
cd ~/OSX-KVM
./OpenCore-Boot-Custom.sh
```

#### Check VM status

```bash
# List running VMs
virsh list

# Or check QEMU processes
ps aux | grep qemu
```

### Requirements

**Host System:**
- Linux (tested on Ubuntu/Debian/Arch)
- QEMU/KVM installed and configured
- Python 3.6+
- Git
- Network connectivity

**macOS VM:**
- macOS (tested on Big Sur, Monterey, Ventura, Sonoma)
- Node.js installed (`brew install node`)
- SSH enabled
- Sufficient disk space

### Credits

- [OSX-KVM](https://github.com/kholia/OSX-KVM) - macOS on QEMU/KVM
- [Mutagen](https://mutagen.io/) - Fast file synchronization
- React Native and Expo teams

### License

These scripts are provided as-is for convenience. Refer to the OSX-KVM repository for licensing information related to macOS virtualization.

### Support

For issues related to:
- **macOS virtualization**: See [OSX-KVM documentation](https://github.com/kholia/OSX-KVM)
- **Mutagen**: See [Mutagen documentation](https://mutagen.io/documentation)
- **These scripts**: Check troubleshooting section above

---
