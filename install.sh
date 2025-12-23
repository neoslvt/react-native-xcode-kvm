#!/bin/bash
# Main installation script for React Native macOS KVM setup
# This script installs mutagen, sets up macOS KVM, and installs the xcode command

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=================================================="
echo -e "${BLUE}React Native macOS KVM Setup${NC}"
echo "=================================================="
echo ""
echo "This script will:"
echo "  1. Install mutagen"
echo "  2. Setup macOS KVM (clone OSX-KVM and create custom boot script)"
echo "  3. Install 'xcode' command to /bin (requires sudo)"
echo ""

# Check for sudo
if [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}Note: Some operations require sudo privileges${NC}"
    echo ""
fi

# Step 1: Install mutagen
echo "=================================================="
echo -e "${GREEN}Step 1: Installing mutagen...${NC}"
echo "=================================================="
echo ""

if command -v mutagen &> /dev/null; then
    echo -e "${GREEN}✓ Mutagen is already installed${NC}"
    mutagen version
else
    echo "Installing mutagen..."
    if python3 install_mutagen.py; then
        echo -e "${GREEN}✓ Mutagen installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install mutagen${NC}" >&2
        echo "You may need to install it manually" >&2
        exit 1
    fi
fi
echo ""

# Step 2: Setup macOS KVM
echo "=================================================="
echo -e "${GREEN}Step 2: Setting up macOS KVM...${NC}"
echo "=================================================="
echo ""

# Check if OSX-KVM already exists
OSX_KVM_DIR="$HOME/OSX-KVM"
if [[ -d "$OSX_KVM_DIR" ]]; then
    echo -e "${YELLOW}OSX-KVM directory already exists at $OSX_KVM_DIR${NC}"
    read -p "Do you want to update it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Setting up/updating macOS KVM..."
        if python3 setup_macos_kvm.py --target-dir "$OSX_KVM_DIR"; then
            echo -e "${GREEN}✓ macOS KVM setup complete${NC}"
        else
            echo -e "${RED}✗ Failed to setup macOS KVM${NC}" >&2
            exit 1
        fi
    else
        echo -e "${YELLOW}Skipping macOS KVM setup${NC}"
        SKIP_DOWNLOAD=true
    fi
else
    echo "Setting up macOS KVM..."
    if python3 setup_macos_kvm.py --target-dir "$OSX_KVM_DIR"; then
        echo -e "${GREEN}✓ macOS KVM setup complete${NC}"
    else
        echo -e "${RED}✗ Failed to setup macOS KVM${NC}" >&2
        exit 1
    fi
fi
echo ""

# Step 2.5: Download macOS (if not skipped)
SKIP_DOWNLOAD=${SKIP_DOWNLOAD:-false}
if [[ "$SKIP_DOWNLOAD" != "true" ]]; then
    echo "=================================================="
    echo -e "${GREEN}Step 2.5: Downloading macOS...${NC}"
    echo "=================================================="
    echo ""
    
    # Function to open new terminal tab
    open_terminal_tab() {
        local cmd="$1"
        local terminal=""
        
        # Detect terminal emulator
        if command -v gnome-terminal &> /dev/null; then
            terminal="gnome-terminal"
            gnome-terminal --tab -- bash -c "cd '$OSX_KVM_DIR' && $cmd; exec bash"
            return 0
        elif command -v konsole &> /dev/null; then
            terminal="konsole"
            konsole --new-tab -e bash -c "cd '$OSX_KVM_DIR' && $cmd; exec bash"
            return 0
        elif command -v xterm &> /dev/null; then
            terminal="xterm"
            xterm -e bash -c "cd '$OSX_KVM_DIR' && $cmd; exec bash" &
            return 0
        elif command -v x-terminal-emulator &> /dev/null; then
            terminal="x-terminal-emulator"
            x-terminal-emulator -e bash -c "cd '$OSX_KVM_DIR' && $cmd; exec bash" &
            return 0
        else
            return 1
        fi
    }
    
    echo -e "${GREEN}Opening new terminal tab for macOS download...${NC}"
    echo ""
    
    if open_terminal_tab "./fetch-macOS-v2.py"; then
        echo -e "${GREEN}✓ Download started in new terminal tab${NC}"
        echo ""
        echo -e "${YELLOW}The macOS download is running in a new terminal tab.${NC}"
        echo -e "${YELLOW}Please wait for the download to complete...${NC}"
        echo ""
        read -p "Press Enter when the macOS download has finished: " -r
        echo ""
    else
        echo -e "${YELLOW}Could not detect terminal emulator for new tab.${NC}"
        echo -e "${YELLOW}Please run the download manually:${NC}"
        echo "  cd $OSX_KVM_DIR"
        echo "  ./fetch-macOS-v2.py"
        echo ""
        read -p "Press Enter when the macOS download has finished: " -r
        echo ""
    fi
    
    # Step 2.6: Convert DMG to IMG (if needed)
    if [[ ! -f "$OSX_KVM_DIR/BaseSystem.img" && -f "$OSX_KVM_DIR/BaseSystem.dmg" ]]; then
        echo -e "${GREEN}Converting BaseSystem.dmg to BaseSystem.img...${NC}"
        if dmg2img -i "$OSX_KVM_DIR/BaseSystem.dmg" "$OSX_KVM_DIR/BaseSystem.img"; then
            echo -e "${GREEN}✓ Conversion complete${NC}"
        else
            echo -e "${YELLOW}Warning: Failed to convert DMG. You may need to do this manually.${NC}"
        fi
        echo ""
    fi
    
    # Step 2.7: Create virtual disk if it doesn't exist
    if [[ ! -f "$OSX_KVM_DIR/mac_hdd_ng.img" ]]; then
        echo -e "${GREEN}Creating virtual disk image...${NC}"
        read -p "Enter disk size (e.g., 256G, default: 256G): " DISK_SIZE
        DISK_SIZE=${DISK_SIZE:-256G}
        if qemu-img create -f qcow2 "$OSX_KVM_DIR/mac_hdd_ng.img" "$DISK_SIZE"; then
            echo -e "${GREEN}✓ Virtual disk created (${DISK_SIZE})${NC}"
        else
            echo -e "${RED}✗ Failed to create virtual disk${NC}" >&2
            exit 1
        fi
        echo ""
    fi
    
    # Step 2.8: Start macOS installation
    echo "=================================================="
    echo -e "${GREEN}Step 2.8: Starting macOS Installation...${NC}"
    echo "=================================================="
    echo ""
    echo -e "${GREEN}Starting macOS VM with installation media...${NC}"
    echo -e "${YELLOW}The VM will start in a new window.${NC}"
    echo -e "${YELLOW}Follow the macOS installation wizard in the VM window.${NC}"
    echo -e "${RED}DON'T FORGET TO NAME THE USER AS 'macos' IN THE MACOS VM.${NC}"
    echo ""
    read -p "Press Enter to start the macOS VM: " -r
    echo ""
    
    # Run the boot script
    cd "$OSX_KVM_DIR"
    if [[ -f "./OpenCore-Boot-Custom.sh" ]]; then
        echo -e "${GREEN}Starting macOS VM...${NC}"
        ./OpenCore-Boot-Custom.sh
    else
        echo -e "${RED}Error: OpenCore-Boot-Custom.sh not found${NC}" >&2
        echo "Please check the OSX-KVM setup." >&2
        exit 1
    fi
fi
echo ""

# Step 3: Install xcode command
echo "=================================================="
echo -e "${GREEN}Step 3: Installing 'xcode' command...${NC}"
echo "=================================================="
echo ""

XCODE_SCRIPT="$SCRIPT_DIR/xcode"
XCODE_INSTALL_PATH="/bin/xcode"

if [[ ! -f "$XCODE_SCRIPT" ]]; then
    echo -e "${RED}Error: xcode script not found at $XCODE_SCRIPT${NC}" >&2
    exit 1
fi

# Check if already installed
if [[ -f "$XCODE_INSTALL_PATH" ]]; then
    echo -e "${YELLOW}xcode command already exists at $XCODE_INSTALL_PATH${NC}"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Skipping xcode installation${NC}"
    else
        echo "Installing xcode command (requires sudo)..."
        if sudo cp "$XCODE_SCRIPT" "$XCODE_INSTALL_PATH" && sudo chmod +x "$XCODE_INSTALL_PATH"; then
            echo -e "${GREEN}✓ xcode command installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install xcode command${NC}" >&2
            exit 1
        fi
    fi
else
    echo "Installing xcode command (requires sudo)..."
    if sudo cp "$XCODE_SCRIPT" "$XCODE_INSTALL_PATH" && sudo chmod +x "$XCODE_INSTALL_PATH"; then
        echo -e "${GREEN}✓ xcode command installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install xcode command${NC}" >&2
        exit 1
    fi
fi
echo ""

# Summary
echo "=================================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=================================================="
echo ""
echo "Installed components:"
echo "  ✓ Mutagen"
echo "  ✓ macOS KVM setup ($OSX_KVM_DIR)"
echo "  ✓ xcode command ($XCODE_INSTALL_PATH)"
echo ""
if [[ "$SKIP_DOWNLOAD" != "true" ]]; then
    echo "Note: macOS installation process has been started."
    echo "Follow the installation wizard in the VM window."
else
    echo "Next steps:"
    echo "  1. Follow the OSX-KVM README to download macOS installer:"
    echo "     cd $OSX_KVM_DIR"
    echo "     ./fetch-macOS-v2.py"
    echo ""
    echo "  2. Create and start your macOS VM:"
    echo "     cd $OSX_KVM_DIR"
    echo "     ./OpenCore-Boot-Custom.sh"
    echo ""
fi
echo ""
echo "  3. In your React Native project directory:"
echo "     xcode add    # Setup mutagen sync and generate run script"
echo "     xcode remove # Remove sync and cleanup"
echo ""
echo "For more information, see README.md"
echo ""

