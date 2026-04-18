#!/bin/bash
# robot.sh - Simple robot launcher

cd /home/pi/trashformer

# Display banner
cat << 'EOF'
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              T R A S H F O R M E R                       ║
║              Autonomous Trash Robot                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

EOF

# Check if running as service
if systemctl is-active --quiet trashformer.service; then
    echo "⚠️  Robot is running as a service!"
    echo ""
    echo "Options:"
    echo "  1. View logs:      sudo journalctl -u trashformer.service -f"
    echo "  2. Stop service:   sudo systemctl stop trashformer.service"
    echo "  3. Restart service: sudo systemctl restart trashformer.service"
    echo ""
    read -p "Stop service and run manually? (y/N): " choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        sudo systemctl stop trashformer.service
        echo "✓ Service stopped"
    else
        exit 0
    fi
fi

# Check for mode argument
if [ -n "$1" ]; then
    MODE="--mode $1"
else
    MODE=""
fi

# Run robot
python3 main.py $MODE