# Quick Start Guide

This guide provides a quick reference for setting up React Native development with macOS in KVM.

## Step-by-Step Setup

### 1. Install Mutagen
```bash
python3 install_mutagen.py
```

### 2. Setup macOS KVM
```bash
python3 setup_macos_kvm.py
cd ~/OSX-KVM
# Follow OSX-KVM instructions to download macOS and create VM disk
./OpenCore-Boot-Custom.sh
```

### 3. Get VM IP Address
After macOS VM is running:
```bash
python3 macos_ssh.py get-ip --port 2222
# Note the IP address (e.g., 10.0.2.15)
export MACOS_VM_IP=10.0.2.15  # Optional: save for later use
```

### 4. Setup File Sync for Your React Native Project
```bash
python3 setup_sync.py ~/path/to/your/react-native-app \
    --macos-ip localhost \
    --macos-port 2222 \
    --macos-user macos
```

### 5. Setup React Native Script for macOS VM

Generate and copy the script to macOS VM:
```bash
./setup.sh
```

This detects your Linux host IP and generates `run_react_native.sh` with it embedded, then copies it to the VM.

### 6. Run React Native

**Option A: On Linux host**
```bash
python3 run_react_native.py ~/path/to/your/react-native-app
```

**Option B: On macOS VM (recommended)**
```bash
# SSH into the VM
python3 macos_ssh.py connect

# Navigate to where script was copied (default: ~/projects)
cd ~/projects

# Run the script
./run_react_native.sh ~/projects/your-app-name

# Or run from project directory
cd ~/projects/your-app-name
./run_react_native.sh
```

### 7. Build and run iOS app on macOS VM
```bash
# If using Expo
npx expo start --ios

# If using React Native CLI
npx react-native run-ios
```

## Common Commands

### Check Mutagen Sync Status
```bash
mutagen sync list
mutagen sync monitor <sync-name>
```

### SSH into macOS VM
```bash
python3 macos_ssh.py connect
# or directly:
ssh -p 2222 macos@localhost
```

### Stop Sync (when done)
```bash
mutagen sync terminate <sync-name>
```

## Troubleshooting

- **Can't connect to VM**: Ensure VM is running and SSH is enabled
- **Sync not working**: Check SSH connectivity with `python3 macos_ssh.py exec "echo test"`
- **React Native can't connect**: Verify `REACT_NATIVE_PACKAGER_HOSTNAME` is set to VM IP

## Tips

- Set `MACOS_VM_IP` environment variable to avoid repeated IP lookups
- Use `mutagen sync monitor` to watch file sync in real-time
- The sync is bidirectional - changes on either side sync automatically

