# Tools Directory

This directory contains development and maintenance tools for calibration, testing, and debugging the Trashformer robotic system. These tools are essential for hardware integration, system validation, and ongoing maintenance of the robot's subsystems.

## Overview

The tools directory provides a comprehensive suite of utilities that support the entire robot development lifecycle:

- **Calibration Tools**: Precise hardware parameter determination for servos, IMU sensors, and cameras
- **Testing Tools**: Component-level and system-level validation scripts
- **Demo Tools**: Interactive demonstrations and capability showcases
- **Diagnostic Tools**: Debugging utilities for troubleshooting hardware and software issues

All tools are designed to work in both simulation and hardware modes, with graceful degradation when hardware is unavailable.

## Directory Structure

```
tools/
├── calibrate_servos.py      # Interactive servo pulse width calibration
├── calibrate_elbow.py       # Specialized elbow joint calibration
├── calibrate_imu.py         # IMU sensor calibration (accel/gyro/mag)
├── test_one_servo_pca.py    # Individual servo testing on PCA9685
├── demo_arm.py              # Comprehensive arm movement demonstrations
├── test_arm_full.py         # Complete arm system functional test
├── test_elbow.py            # Elbow joint specific testing
├── test_sabertooth.py       # Sabertooth motor controller validation
├── test_servos.py           # Servo testing without PCA9685 driver
├── test_sensors.py          # Multi-sensor testing and validation
├── arm_poke.py              # Simple interactive arm control
└── camera_preview.py        # Camera feed preview and diagnostics
```

## Detailed Tool Documentation

### Calibration Tools

#### calibrate_servos.py
**Purpose**: Interactive calibration of servo pulse widths and direction for accurate positioning.

**What it does**:
- Tests each servo (shoulder, elbow, gripper) individually
- Finds actual minimum/maximum pulse widths (not assuming standard 500-2500μs)
- Determines if servos are inverted (direction reversed)
- Generates configuration updates for `config/default.yaml`

**Technical Details**:
- Uses PCA9685 driver directly for precise pulse control
- Tests common pulse ranges: 500-2700μs for min/max finding
- Calculates center position as (min+max)/2
- Validates servo direction by asking user to observe movement

**Usage**:
```bash
cd /path/to/trashformer
python tools/calibrate_servos.py
```

**Prerequisites**:
- Servos connected to PCA9685 channels 0, 1, 2
- External 5V servo power supply (NOT Raspberry Pi 5V)
- Arm has clear space to move through full range
- User ready to observe and respond to prompts

**Output**: Updates `config/default.yaml` with:
```yaml
arm:
  pwm_limits:
    min_pulse: 600    # Actual minimum found
    max_pulse: 2400   # Actual maximum found
```

**Debugging**:
- If servo doesn't move: Check PCA9685 I2C connection, servo power, wiring
- If servo moves erratically: Verify external power supply voltage stability
- If calibration values seem wrong: Check for servo brand/model differences

**Files Used**:
- `arm/pca9685_driver.py` - Hardware PWM control
- `utils/logger.py` - Logging output
- `config/default.yaml` - Configuration updates

#### calibrate_imu.py
**Purpose**: Calibrate IMU (Inertial Measurement Unit) sensors for accurate orientation and motion tracking.

**What it does**:
- Collects accelerometer, gyroscope, and magnetometer data
- Calculates offset corrections for zero-point calibration
- Generates calibration file for sensor fusion accuracy

**Technical Details**:
- Uses IMU sensor fusion algorithms
- Requires robot to be held in specific orientations (6-point calibration)
- Calculates bias offsets and scale factors
- Outputs JSON calibration data

**Usage**:
```bash
python tools/calibrate_imu.py
```

**Prerequisites**:
- IMU sensor properly mounted and connected
- Robot stable and level surface available
- User can rotate robot through calibration positions

**Output**: Creates `data/calibration/imu_offsets.json`:
```json
{
  "accelerometer": {"x": 0.02, "y": -0.01, "z": 0.03},
  "gyroscope": {"x": 1.2, "y": -0.8, "z": 0.5},
  "magnetometer": {"x": 15.3, "y": -8.7, "z": 22.1}
}
```

**Debugging**:
- If calibration fails: Check IMU I2C connection and address
- If offsets are extreme: Verify IMU mounting orientation
- If sensor fusion is inaccurate: Recalibrate and check for magnetic interference

**Files Used**:
- `sensors/imu.py` - IMU sensor interface
- `data/calibration/imu_offsets.json` - Calibration output
- `utils/config_loader.py` - Configuration loading

### Testing Tools

#### test_arm_full.py
**Purpose**: Complete functional test of the robotic arm system including all joints and movements.

**What it does**:
- Executes predefined sequence of arm movements
- Tests shoulder, elbow, and gripper coordination
- Validates trajectory execution and positioning accuracy
- Provides visual confirmation of proper operation

**Test Sequence**:
1. Home position (shoulder: 0°, elbow: 0°, gripper: open)
2. Open/close gripper test
3. Shoulder to horizontal (90°)
4. Elbow to right (90°)
5. Gripper open/close at extended position
6. Return elbow to center (0°)
7. Return shoulder to down (0°)

**Technical Details**:
- Uses ArmController with real hardware (simulate=False)
- Configurable speed and delay parameters
- Blocking movements with status logging
- Safe return-to-home on completion

**Usage**:
```bash
python tools/test_arm_full.py
```

**Prerequisites**:
- All arm servos connected and powered
- Clear space for arm movement (avoid obstacles)
- External servo power supply
- Robot on stable surface

**Expected Output**:
```
Servo Channel Mapping:
  shoulder: Channel 0
  elbow: Channel 1
  gripper: Channel 2

Step 0: Going to HOME position
Step 1: Opening gripper
Step 2: Closing gripper
...
✅ SIMPLE ARM TEST COMPLETE
```

**Debugging**:
- If servo doesn't move: Check PCA9685 connection and power
- If movement is jerky: Verify servo calibration and power stability
- If positions are wrong: Recalibrate servos with calibrate_servos.py
- If arm collides: Check workspace clearance and pose definitions

**Files Used**:
- `arm/arm_controller.py` - Main arm control interface
- `utils/config_loader.py` - Configuration loading
- `utils/logger.py` - Test progress logging
- `config/default.yaml` - Hardware configuration

#### test_sensors.py
**Purpose**: Comprehensive testing of all sensor systems including IMU, TOF, ultrasonic, and limit switches.

**What it does**:
- Tests each sensor type individually
- Validates sensor readings and data formats
- Checks sensor fusion integration
- Provides diagnostic output for troubleshooting

**Technical Details**:
- Tests IMU (accelerometer, gyroscope, magnetometer)
- Tests distance sensors (TOF, ultrasonic)
- Tests limit switches and encoders
- Validates sensor data ranges and update rates

**Usage**:
```bash
python tools/test_sensors.py
```

**Prerequisites**:
- All sensors connected and powered
- Clear environment for distance sensor testing
- Robot can be moved for encoder testing

**Expected Output**:
```
Testing IMU...
  Accelerometer: x=0.01, y=0.02, z=9.81
  Gyroscope: x=0.1, y=-0.2, z=0.0
  Magnetometer: x=15.3, y=-8.7, z=22.1

Testing TOF sensors...
  Front: 1250mm
  Left: 890mm
  Right: 756mm

Testing ultrasonic...
  Rear: 2340mm

Testing limit switches...
  Shoulder limit: OK
  Elbow limit: OK
  Gripper limit: OK
```

**Debugging**:
- If IMU fails: Check I2C connection, recalibrate with calibrate_imu.py
- If distance sensors fail: Check power, wiring, check for interference
- If encoders fail: Verify motor connections and encoder wiring
- If readings are erratic: Check for electrical noise or sensor damage

**Files Used**:
- `sensors/imu.py` - IMU testing
- `sensors/tof.py` - TOF sensor testing
- `sensors/ultrasonic.py` - Ultrasonic testing
- `sensors/limit_switches.py` - Switch testing
- `drive/encoders.py` - Encoder testing

#### test_sabertooth.py
**Purpose**: Validation of Sabertooth motor controller for drive system.

**What it does**:
- Tests motor controller communication
- Validates motor direction and speed control
- Checks encoder feedback integration
- Tests emergency stop functionality

**Technical Details**:
- Uses serial communication with Sabertooth
- Tests motor ramping and braking
- Validates encoder count accuracy
- Tests watchdog timeout behavior

**Usage**:
```bash
python tools/test_sabertooth.py
```

**Prerequisites**:
- Sabertooth controller connected via serial
- Motors connected and powered
- Encoders connected (if available)
- Clear space for motor testing

**Expected Output**:
```
Sabertooth Test Starting...
Motor 1: Forward 50% - OK
Motor 1: Reverse 50% - OK
Motor 2: Forward 50% - OK
Motor 2: Reverse 50% - OK
Encoder counts: Motor1=1250, Motor2=1180
Emergency stop test - OK
```

**Debugging**:
- If no response: Check serial connection and baud rate
- If motors don't move: Verify motor power and wiring
- If encoders fail: Check encoder connections and configuration
- If communication errors: Verify serial port and controller address

**Files Used**:
- `drive/sabertooth_serial.py` - Motor controller interface
- `drive/encoders.py` - Encoder feedback
- `safety/estop.py` - Emergency stop testing

### Demo Tools

#### demo_arm.py
**Purpose**: Comprehensive demonstration of arm capabilities including poses, sequences, and interactive control.

**What it does**:
- Demonstrates basic arm movements and poses
- Shows gripper control and positioning
- Executes complete trash pickup sequences
- Provides interactive keyboard control mode

**Available Demos**:
- `basic`: Home, ready, and rest positions
- `gripper`: Open/close and partial grip control
- `manual`: Individual servo angle control
- `pickup`: Complete trash pickup sequence
- `reach`: Directional reaching movements
- `wave`: Fun waving animation
- `calibrate`: Calibration pose testing
- `interactive`: Keyboard control mode

**Technical Details**:
- Uses ArmController with configurable simulation/hardware mode
- Supports pose-based movement with speed control
- Implements sequence execution with error handling
- Interactive mode with command parsing

**Usage**:
```bash
# Run all demos
python tools/demo_arm.py

# Run specific demo
python tools/demo_arm.py --demo pickup

# Interactive mode
python tools/demo_arm.py --demo interactive

# Simulation mode (no hardware)
python tools/demo_arm.py --simulate
```

**Prerequisites**:
- Arm hardware connected (unless --simulate used)
- Clear workspace for movement
- User interaction for interactive mode

**Interactive Commands**:
- `h` - Home position
- `r` - Ready position
- `o` - Open gripper
- `c` - Close gripper
- `p` - Pickup sequence
- `w` - Wave animation
- `l` - List all poses
- `[pose_name]` - Go to named pose
- `q` - Quit

**Debugging**:
- If poses fail: Check pose definitions in `arm/poses.yaml`
- If movements are wrong: Verify servo calibration
- If sequences fail: Check pose transitions and workspace limits
- If interactive mode fails: Verify keyboard input handling

**Files Used**:
- `arm/arm_controller.py` - Arm control interface
- `arm/poses.yaml` - Pose definitions
- `utils/config_loader.py` - Configuration
- `utils/logger.py` - Demo logging

### Diagnostic Tools

#### arm_poke.py
**Purpose**: Simple interactive arm control for quick testing and debugging.

**What it does**:
- Provides direct servo control interface
- Allows manual positioning for troubleshooting
- Tests individual joint movement
- Quick verification of arm functionality

**Technical Details**:
- Direct servo angle commands
- Real-time position feedback
- Simple command interface
- Immediate movement execution

**Usage**:
```bash
python tools/arm_poke.py
```

**Prerequisites**:
- Arm servos connected and powered
- Clear space for movement
- User ready for interactive control

**Expected Output**:
```
Arm Poke Test
Commands: s<angle> e<angle> g<angle> h q
> s45
Shoulder to 45°
> e90
Elbow to 90°
> g50
Gripper to 50°
```

**Debugging**:
- If commands fail: Check servo connections and power
- If positions wrong: Verify calibration and angle limits
- If movement jerky: Check power supply stability

**Files Used**:
- `arm/arm_controller.py` - Basic arm control
- `utils/logger.py` - Command logging

#### camera_preview.py
**Purpose**: Camera feed preview and basic image processing diagnostics.

**What it does**:
- Displays live camera feed
- Shows image processing results
- Tests camera connectivity and configuration
- Validates vision pipeline input

**Technical Details**:
- Uses OpenCV for camera capture and display
- Shows raw camera feed with overlays
- Tests different resolutions and frame rates
- Basic image processing validation

**Usage**:
```bash
python tools/camera_preview.py
```

**Prerequisites**:
- Camera connected (USB or CSI)
- OpenCV installed
- Display available for preview

**Expected Output**: Live camera window with feed and diagnostics.

**Debugging**:
- If no camera: Check camera connection and permissions
- If distorted image: Verify camera configuration and calibration
- If processing fails: Check OpenCV installation and camera format

**Files Used**:
- `vision/camera.py` - Camera interface
- `vision/vision_config.yaml` - Camera configuration

## Configuration and Dependencies

### Required Python Packages
```bash
pip install opencv-python numpy pyyaml pyserial smbus2
```

### Hardware Configuration
All tools read from `config/default.yaml` for hardware parameters:
- PCA9685 I2C address and frequency
- Servo channel mappings and limits
- Sensor I2C addresses and calibration files
- Motor controller serial settings

### Environment Variables
```bash
export PYTHONPATH=/path/to/trashformer:$PYTHONPATH
```

## Advanced Usage Patterns

### Automated Testing Pipeline
```bash
#!/bin/bash
# Run complete system validation
python tools/test_sensors.py
python tools/test_arm_full.py
python tools/test_sabertooth.py
python tools/demo_arm.py --demo pickup
```

### Calibration Workflow
```bash
#!/bin/bash
# Complete robot calibration
python tools/calibrate_imu.py
python tools/calibrate_servos.py
python tools/camera_preview.py  # Manual camera focus/check
```

### Remote Diagnostics
```bash
# Save sensor logs for analysis
python tools/test_sensors.py --save-log sensor_data.csv
# Transfer logs to development machine
scp sensor_data.csv dev-machine:~/debug/
```

## Troubleshooting Common Issues

### Hardware Connection Problems
**Symptom**: Tools fail with "No device found" or "I2C error"
**Solutions**:
1. Check physical connections (I2C, serial, power)
2. Verify device addresses in configuration
3. Test with `i2cdetect -y 1` (Linux) or I2C scanner
4. Check power supply voltage and stability

### Servo Movement Issues
**Symptom**: Servos don't move or move erratically
**Solutions**:
1. Run `tools/test_one_servo_pca.py` to isolate issues
2. Check external power supply (not Pi 5V)
3. Verify PCA9685 connection: `i2cdetect -y 1`
4. Recalibrate with `tools/calibrate_servos.py`
5. Check servo wiring and channel assignments

### Sensor Reading Problems
**Symptom**: Sensors return invalid or no data
**Solutions**:
1. Run `tools/test_sensors.py` for individual sensor testing
2. Check sensor power and wiring
3. Verify I2C addresses and bus conflicts
4. Recalibrate IMU with `tools/calibrate_imu.py`
5. Check for electromagnetic interference

### Communication Errors
**Symptom**: Serial or I2C communication failures
**Solutions**:
1. Verify baud rates and serial port configuration
2. Check cable connections and quality
3. Test with minimal example code
4. Monitor with protocol analyzer if available

### Performance Issues
**Symptom**: Tools run slowly or with delays
**Solutions**:
1. Check CPU usage and memory availability
2. Verify real-time kernel (if required)
3. Profile code execution with timing tools
4. Optimize I2C/Serial communication settings

## Development Guidelines

### Adding New Tools
1. Follow naming convention: `test_*.py`, `calibrate_*.py`, `demo_*.py`
2. Include comprehensive docstrings and help text
3. Add command-line argument parsing with `--help`
4. Implement proper error handling and logging
5. Document hardware prerequisites and expected outputs
6. Update this README with tool description and usage

### Tool Architecture Best Practices
- Use configuration files for hardware parameters
- Implement simulation mode for development
- Provide clear user feedback and progress indication
- Handle missing hardware gracefully
- Include comprehensive error messages
- Support logging to files for debugging

### Testing Tool Quality
- Verify tools work in both simulation and hardware modes
- Test with partial hardware configurations
- Validate error handling with disconnected hardware
- Ensure tools clean up resources properly
- Check for memory leaks in long-running tools

## Integration with Main System

### Configuration Sharing
Tools use the same configuration files as the main system:
- `config/default.yaml` - Base configuration
- `config/hardware_config.yaml` - Hardware-specific overrides
- `data/calibration/` - Calibration data storage

### Logging Integration
All tools use the centralized logging system:
- `utils/logger.py` - Logging configuration
- Consistent log levels and formatting
- Log rotation and file management

### Error Handling
Tools follow consistent error handling patterns:
- Custom exceptions for hardware-specific errors
- Graceful degradation when hardware unavailable
- Clear error messages with troubleshooting guidance
- Exit codes indicating success/failure status

## Performance Monitoring

### Benchmarking Tools
```bash
# Time arm movement execution
time python tools/test_arm_full.py

# Monitor system resources during testing
python tools/test_sensors.py &
top -p $!
```

### Profiling Execution
```bash
# Profile tool performance
python -m cProfile tools/test_arm_full.py

# Memory usage analysis
python -m memory_profiler tools/demo_arm.py
```

## Security Considerations

### Hardware Safety
- Tools include safety checks before hardware access
- Emergency stop integration where applicable
- Power sequencing validation
- Movement bounds checking

### Data Handling
- Calibration data stored securely
- No sensitive information in logs
- Safe defaults for uncalibrated hardware
- Validation of input parameters

## Future Enhancements

### Planned Tool Improvements
- GUI interfaces for interactive tools
- Automated calibration procedures
- Performance benchmarking suite
- Remote monitoring and control
- Data logging and analysis tools
- Hardware abstraction layer testing

### Integration Opportunities
- CI/CD pipeline integration
- Automated testing frameworks
- Performance regression detection
- Remote diagnostics and updates
- Hardware health monitoring

This comprehensive tool suite ensures reliable development, testing, and maintenance of the Trashformer robotic system, providing developers and operators with the utilities needed for successful robot operation and troubleshooting.
