#!/bin/bash
# setup_autostart.sh - Configure robot to start automatically on boot

echo "Setting up Trashformer auto-start..."

# Create systemd service file
sudo tee /etc/systemd/system/trashformer.service > /dev/null << 'EOF'
[Unit]
Description=Trashformer Robot Controller
After=network.target bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/trashformer
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /home/pi/trashformer/main.py --mode gamepad
Restart=on-failure
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo "✓ Service file created"
echo ""
echo "Available commands:"
echo ""
echo "  Enable auto-start (run on boot):"
echo "    sudo systemctl enable trashformer.service"
echo ""
echo "  Start service now:"
echo "    sudo systemctl start trashformer.service"
echo ""
echo "  Stop service:"
echo "    sudo systemctl stop trashformer.service"
echo ""
echo "  Check status:"
echo "    sudo systemctl status trashformer.service"
echo ""
echo "  View logs:"
echo "    sudo journalctl -u trashformer.service -f"
echo ""
echo "  Disable auto-start:"
echo "    sudo systemctl disable trashformer.service"
echo ""
echo "To change mode, edit: /etc/systemd/system/trashformer.service"
echo "Available modes: gamepad, teleop, autonomous, test, interactive"