#!/bin/bash
"""
Install RoboClaw Library
========================

Downloads and installs the BasicMicro RoboClaw Python library
"""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ROBOCLAW LIBRARY INSTALLATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Install pyserial
echo "1. Installing pyserial..."
pip3 install pyserial --break-system-packages

# Download RoboClaw library
echo ""
echo "2. Downloading RoboClaw library from BasicMicro..."
cd /tmp
wget -q https://downloads.basicmicro.com/code/roboclaw_python.zip

if [ $? -ne 0 ]; then
    echo "❌ Download failed. Trying alternative method..."
    echo ""
    echo "Manual download:"
    echo "1. Go to: https://www.basicmicro.com/downloads"
    echo "2. Download: roboclaw_python.zip"
    echo "3. Copy roboclaw.py to ~/trashformer/drive/"
    exit 1
fi

# Extract
echo "3. Extracting..."
unzip -q roboclaw_python.zip

# Copy to project
echo "4. Installing to project..."
mkdir -p ~/trashformer/drive
cp roboclaw.py ~/trashformer/drive/

# Also install system-wide
echo "5. Installing system-wide..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
sudo cp roboclaw.py /usr/local/lib/python${PYTHON_VERSION}/dist-packages/

# Clean up
rm -f roboclaw_python.zip roboclaw.py

# Test
echo ""
echo "6. Testing installation..."
python3 -c "from roboclaw import Roboclaw; print('✓ RoboClaw library loaded successfully')"

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ INSTALLATION COMPLETE!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "RoboClaw library installed to:"
    echo "  - ~/trashformer/drive/roboclaw.py"
    echo "  - /usr/local/lib/python${PYTHON_VERSION}/dist-packages/roboclaw.py"
    echo ""
    echo "You can now use: from roboclaw import Roboclaw"
    echo ""
else
    echo ""
    echo "❌ Installation failed. Please install manually."
    echo ""
    echo "Manual steps:"
    echo "1. Download from: https://www.basicmicro.com/downloads"
    echo "2. Extract roboclaw.py"
    echo "3. Copy to: ~/trashformer/drive/roboclaw.py"
    echo ""
fi