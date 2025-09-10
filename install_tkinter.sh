#!/bin/bash

echo "🔧 Installing tkinter and GUI support..."
echo "======================================="

# Update package lists
echo "📦 Updating package lists..."
sudo apt update

# Install tkinter and dependencies
echo "📦 Installing Python tkinter..."
sudo apt install -y python3-tk python3-full

# Install additional GUI dependencies
echo "📦 Installing additional GUI libraries..."
sudo apt install -y python3-pil python3-pil.imagetk

# Verify installation
echo "✅ Verifying tkinter installation..."
python3 -c "import tkinter; print('✅ tkinter installed successfully')" || echo "❌ tkinter installation failed"

# Check Python version
echo "🐍 Python version:"
python3 --version

# Display setup instructions
echo ""
echo "🎯 Next Steps for GUI Support:"
echo "==============================="
echo "For WSL GUI support, you need an X server:"
echo ""
echo "Option 1: VcXsrv (Recommended)"
echo "  1. Download VcXsrv: https://sourceforge.net/projects/vcxsrv/"
echo "  2. Run XLaunch with these settings:"
echo "     - Display number: -1"
echo "     - Start no client: ✓"
echo "     - Disable access control: ✓"
echo "  3. Add to ~/.bashrc:"
echo "     export DISPLAY=\$(ip route list default | awk '{print \$3}'):0"
echo "     export LIBGL_ALWAYS_INDIRECT=1"
echo "  4. Restart WSL: wsl --shutdown"
echo ""
echo "Option 2: Windows 11 WSLg"
echo "  - Should work automatically on Windows 11"
echo ""
echo "Test with: python3 main.py"
echo ""
echo "✨ Installation completed!"