# Launch Scripts Directory

This directory contains shell scripts for launching the Trashformer robot in different operational modes. These scripts handle system initialization, environment setup, and process management for safe and reliable robot operation.

## Launch Scripts Overview

```
launch/
├── start_robot.sh      # Complete system startup
├── autonomous.sh       # Autonomous trash pickup mode
├── teleop.sh          # Teleoperation (remote control) mode
├── simulation.sh      # Hardware-free simulation
└── README.md          # This documentation
```

## Script Details and Usage

### **start_robot.sh** - Complete System Startup
Master startup script that initializes the entire robot system with all hardware and software components.

**What it does:**
1. **Environment setup**: Set Python path, environment variables
2. **Hardware initialization**: Start motor controllers, sensors, servos
3. **Calibration loading**: Load camera, IMU, servo calibration data
4. **System checks**: Verify all components are responding
5. **Main application**: Launch the core robot control system
6. **Monitoring**: Start health monitoring and logging

**Usage:**
```bash
# Start complete robot system
./launch/start_robot.sh

# With debug output
DEBUG=1 ./launch/start_robot.sh

# Start in safe mode (reduced functionality)
SAFE_MODE=1 ./launch/start_robot.sh
```

**Expected output:**
```
Trashformer Robot System Starting...
[INFO] Loading configuration from config/default.yaml
[INFO] Initializing hardware subsystems...
[INFO] Camera: OK
[INFO] IMU: OK
[INFO] Motor controllers: OK
[INFO] Servos: OK
[INFO] System ready. Starting autonomous operation...
```

**Environment variables:**
- `DEBUG=1`: Enable verbose logging
- `SAFE_MODE=1`: Disable autonomous features, enable extra safety checks
- `CONFIG_FILE=path`: Use custom configuration file
- `LOG_LEVEL=DEBUG`: Set logging verbosity

**Location:** `launch/start_robot.sh`

### **autonomous.sh** - Autonomous Operation Mode
Launch script for fully autonomous trash detection and pickup operation.

**What it does:**
1. **System startup**: Run full system initialization
2. **Vision system**: Enable camera and object detection
3. **Behavior system**: Start autonomous state machine
4. **Navigation**: Enable self-driving capabilities
5. **Safety systems**: Ensure all safety interlocks active
6. **Logging**: Record autonomous operation data

**Usage:**
```bash
# Start autonomous mode
./launch/autonomous.sh

# Start with specific search area
SEARCH_AREA="kitchen" ./launch/autonomous.sh

# Start with debug visualization
DEBUG_VISION=1 ./launch/autonomous.sh
```

**Operational modes:**
- **Full autonomous**: Complete trash pickup cycle
- **Search only**: Just detect and locate trash
- **Pickup only**: Manual targeting, automatic pickup
- **Navigation only**: Drive to waypoints

**Configuration options:**
- `SEARCH_AREA`: Define operating area (kitchen, office, etc.)
- `MAX_RUNTIME`: Limit operation time (seconds)
- `DEBUG_VISION`: Show camera feed and detections
- `RECORD_VIDEO`: Save operation video

**Location:** `launch/autonomous.sh`

### **teleop.sh** - Teleoperation Mode
Launch script for manual remote control operation using gamepad, keyboard, or other input devices.

**What it does:**
1. **System startup**: Initialize hardware (but not autonomous systems)
2. **Input devices**: Detect and configure gamepads/keyboards
3. **Control mapping**: Set up control bindings
4. **Safety limits**: Enable teleop-specific safety features
5. **Feedback**: Provide operator feedback and status

**Supported input methods:**
- **Gamepad**: Xbox/PS4 controllers (primary method)
- **Keyboard**: WASD/arrows for movement, keys for arm control
- **Joystick**: Professional RC controllers
- **Touchscreen**: On-robot control interface

**Usage:**
```bash
# Start teleoperation
./launch/teleop.sh

# Specify input device
INPUT_DEVICE="gamepad" ./launch/teleop.sh

# Enable training mode (reduced speed)
TRAINING_MODE=1 ./launch/teleop.sh
```

**Control mappings (default gamepad):**
- **Left stick**: Robot movement (forward/back, turn)
- **Right stick**: Camera pan/tilt (if available)
- **Triggers**: Arm raise/lower
- **Buttons**: Gripper open/close, emergency stop
- **D-pad**: Fine movement adjustments

**Safety features:**
- **Speed limiting**: Reduced max speeds for safety
- **Dead zones**: Prevent accidental movement
- **E-stop**: Immediate stop on button press
- **Heartbeat**: Require continuous operator input

**Location:** `launch/teleop.sh`

### **simulation.sh** - Simulation Environment
Launch script for running the robot software without physical hardware, using simulated sensors and actuators.

**What it does:**
1. **Mock hardware**: Replace real hardware with simulators
2. **Virtual environment**: Create 3D simulation world
3. **Sensor simulation**: Generate realistic sensor data
4. **Visualization**: Show robot state and environment
5. **Testing framework**: Enable automated testing

**Simulation capabilities:**
- **Physics simulation**: Realistic robot movement and interactions
- **Sensor modeling**: Camera images, IMU data, distance sensors
- **Environment modeling**: Rooms, obstacles, trash objects
- **Real-time visualization**: 3D view of robot and environment

**Usage:**
```bash
# Start simulation
./launch/simulation.sh

# Load specific environment
WORLD_FILE="kitchen.world" ./launch/simulation.sh

# Enable GUI visualization
GUI=1 ./launch/simulation.sh

# Run automated tests
TEST_MODE=1 ./launch/simulation.sh
```

**Simulation modes:**
- **Interactive**: Manual control with visualization
- **Automated**: Run test scenarios automatically
- **Headless**: No GUI, for CI/CD testing
- **Replay**: Replay recorded operation data

**Environment files:**
- `worlds/kitchen.world`: Kitchen environment with tables, chairs
- `worlds/office.world`: Office space with desks and wastebaskets
- `worlds/outdoor.world`: Outdoor area with various terrain

**Location:** `launch/simulation.sh`

## Common Launch Issues and Debugging

### Issue: Script won't execute (permission denied)

**Symptoms:**
```
bash: ./launch/start_robot.sh: Permission denied
```

**Fix:**
```bash
# Make scripts executable
chmod +x launch/*.sh

# Or make all scripts executable
find launch/ -name "*.sh" -exec chmod +x {} \;
```

### Issue: Python module not found

**Symptoms:**
```
ImportError: No module named 'trashformer'
```

**Debug:**
```bash
# Check Python path
echo $PYTHONPATH

# Add project to path
export PYTHONPATH="$PWD:$PYTHONPATH"

# Check Python version
python --version

# Verify virtual environment
which python
which pip
```

**Fix:**
- Activate virtual environment
- Install missing dependencies: `pip install -r requirements.txt`
- Check Python path in script

### Issue: Hardware not detected

**Symptoms:**
```
[ERROR] Camera not found
[ERROR] Motor controller not responding
```

**Debug:**
```bash
# Check USB devices
lsusb

# Check serial ports
ls /dev/tty*

# Test individual components
python tools/test_sensors.py
python tools/test_drive.py
python tools/camera_preview.py
```

**Common causes:**
- USB cables loose
- Power not connected
- Device permissions (run as root or fix udev rules)
- Hardware failure

### Issue: System starts but crashes immediately

**Symptoms:**
- System initializes successfully
- Then crashes within seconds
- Error messages about configuration or calibration

**Debug:**
```bash
# Run with verbose logging
DEBUG=1 ./launch/start_robot.sh

# Check configuration files
python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"

# Validate calibration data
python -c "import json; json.load(open('data/calibration/camera_params.json'))"

# Test individual modules
python -c "from robot.robot_system import RobotSystem; r = RobotSystem()"
```

**Common causes:**
- Invalid configuration YAML
- Corrupted calibration data
- Missing model files
- Hardware communication issues

### Issue: Autonomous mode doesn't find trash

**Symptoms:**
- Robot moves but never picks up trash
- Vision system reports no detections

**Debug:**
```bash
# Test vision system separately
python tools/camera_preview.py

# Check model file exists
ls -la models/trash_detector.pt

# Test detection manually
python -c "from vision.detector import TrashDetector; d = TrashDetector()"

# Check confidence threshold
grep confidence_threshold config/vision_config.yaml
```

**Fix:**
- Recalibrate camera
- Retrain or download new model
- Adjust detection parameters
- Improve lighting conditions

### Issue: Teleop controls not responding

**Symptoms:**
- Gamepad connected but no movement
- Buttons work but axes don't

**Debug:**
```bash
# List input devices
ls /dev/input/

# Test gamepad
jstest /dev/input/js0

# Check event codes
evtest /dev/input/event3

# Run teleop with debug
DEBUG=1 ./launch/teleop.sh
```

**Fix:**
- Different gamepad mapping required
- Dead zone calibration needed
- Input device permissions
- Driver issues

### Issue: Simulation crashes or runs slowly

**Symptoms:**
- Simulation won't start
- Runs at <5 FPS
- Graphics glitches

**Debug:**
```bash
# Check OpenGL/drivers
glxinfo | grep version

# Test basic graphics
python -c "import pygame; pygame.init()"

# Run minimal simulation
HEADLESS=1 ./launch/simulation.sh

# Check system resources
top -p $(pgrep -f simulation)
```

**Fix:**
- Update graphics drivers
- Reduce simulation complexity
- Run headless for testing
- Check system requirements

## Launch Script Architecture

### **Common Script Structure**
All launch scripts follow this pattern:

```bash
#!/bin/bash
set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment
source "$PROJECT_ROOT/setup_env.sh"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --debug) DEBUG=1 ;;
    --config=*) CONFIG_FILE="${1#*=}" ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export LOG_LEVEL=${DEBUG:+DEBUG}

# Hardware checks (for real hardware scripts)
if [ "$USE_HARDWARE" = "1" ]; then
    check_hardware || exit 1
fi

# Launch application
cd "$PROJECT_ROOT"
python -m robot.main "$@"
```

### **Environment Setup**
Shared environment configuration in `setup_env.sh`:

```bash
# Python environment
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export VIRTUAL_ENV="$PROJECT_ROOT/venv"

# Hardware configuration
export USE_HARDWARE=1
export CAMERA_DEVICE=/dev/video0
export MOTOR_CONTROLLER_PORT=/dev/ttyUSB0

# Logging
export LOG_DIR="$PROJECT_ROOT/logs"
export LOG_LEVEL=INFO

# Safety
export ENABLE_SAFETY=1
export ESTOP_PIN=17
```

### **Process Management**
Launch scripts handle:
- **Background processes**: Start daemons and services
- **Process groups**: Group related processes
- **Signal handling**: Graceful shutdown on Ctrl+C
- **Health monitoring**: Restart crashed processes
- **Resource limits**: CPU/memory limits per process

## Advanced Usage

### **Custom Launch Configurations**
```bash
# Create custom config
cat > my_config.yaml << EOF
robot:
  mode: autonomous
  search_area: [0, 0, 10, 10]
  max_speed: 0.5

vision:
  confidence_threshold: 0.6
  camera_resolution: [1280, 720]
EOF

# Launch with custom config
CONFIG_FILE=my_config.yaml ./launch/autonomous.sh
```

### **Remote Launch**
```bash
# Launch on remote robot
ssh robot@trashformer.local "./launch/start_robot.sh"

# With port forwarding for visualization
ssh -L 8080:localhost:8080 robot@trashformer.local "./launch/teleop.sh"
```

### **Launch with Profiling**
```bash
# Profile Python performance
PYTHONPROFILE=1 ./launch/autonomous.sh

# Memory profiling
MEMORY_PROFILE=1 ./launch/simulation.sh

# Generate flame graphs
PERF_RECORD=1 ./launch/start_robot.sh
```

## Where to Find Everything

**Main launch scripts:** `launch/*.sh`
- `start_robot.sh`: Full system startup
- `autonomous.sh`: Autonomous operation
- `teleop.sh`: Manual control
- `simulation.sh`: Hardware-free testing

**Configuration files:** `config/*.yaml`
- `default.yaml`: Base configuration
- `hardware_config.yaml`: Hardware-specific settings

**Environment setup:** `setup_env.sh` (if exists)
- Shared environment variables and paths

**Log files:** `logs/trashformer_*.log`
- Startup logs, error messages, performance data

**Test tools:** `tools/*.py`
- Individual component testing
- Calibration utilities

## Development and Testing

### **Testing Launch Scripts**
```bash
# Syntax check
bash -n launch/start_robot.sh

# Dry run (show what would execute)
DRY_RUN=1 ./launch/start_robot.sh

# Test in simulation first
./launch/simulation.sh --test
```

### **Adding New Launch Scripts**
1. Copy existing script as template
2. Modify environment variables
3. Update command-line arguments
4. Add script-specific checks
5. Test thoroughly before deployment

### **Launch Script Best Practices**
- Always check for required files
- Provide clear error messages
- Support --help and --version
- Clean up on exit (trap signals)
- Log important events
- Validate configuration before starting

Each script can reference configuration from:
- `../config/` - Base configuration files
- Environment variables - System-specific settings
- Command-line arguments - Per-run customization

## Troubleshooting

If scripts fail to start:
1. Check permissions: `chmod +x *.sh`
2. Verify Python environment is activated
3. Check hardware connections
4. Review launch logs in `../logs/`

## Example: Custom Launch
```bash
CONFIG=development.yaml ./launch/autonomous.sh --log-level DEBUG
```
