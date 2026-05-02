# Documentation Directory

This directory contains all documentation for the Trashformer robotic system, from high-level overviews to detailed technical specifications. The documentation is organized to support different user types: developers, operators, and maintainers.

## Documentation Structure

```
docs/
├── README.md           # This file - documentation guide
├── setup.md            # Installation and setup procedures
├── hardware.md         # Hardware specifications and connections
├── api.md              # API reference for all modules
├── troubleshooting.md  # Problem diagnosis and solutions
├── design/             # Design documents (if exists)
└── images/             # Diagrams and photos (if exists)
```

## Documentation Files - Detailed Guide

### **setup.md** - System Setup and Installation
Comprehensive guide for getting the Trashformer system up and running from scratch. This is the first document to read for new installations.

**Should contain:**
- **Prerequisites**: Required hardware, software dependencies
- **Installation steps**: Step-by-step setup procedures
- **Configuration**: Initial configuration and calibration
- **Testing**: Verification that installation was successful
- **Troubleshooting**: Common setup issues and solutions

**Typical structure:**
```markdown
# System Setup Guide

## Prerequisites
- Raspberry Pi 4B with 4GB RAM
- Ubuntu 20.04 or Raspberry Pi OS
- Python 3.8+
- Required hardware components

## Software Installation
### 1. OS Setup
### 2. Python Environment
### 3. Dependencies
### 4. Project Installation

## Hardware Assembly
### 1. Mechanical Assembly
### 2. Electrical Connections
### 3. Power Systems

## Initial Configuration
### 1. Network Setup
### 2. Hardware Configuration
### 3. Calibration Procedures

## Testing and Verification
### 1. Hardware Tests
### 2. Software Tests
### 3. Integration Tests

## Common Setup Issues
- Permission problems
- Dependency conflicts
- Hardware connection issues
```

**Location:** `docs/setup.md`

**When to use:**
- First-time system setup
- Hardware changes or upgrades
- Recovery from system failures
- Setting up development environments

### **hardware.md** - Hardware Specifications and Connections
Detailed technical specifications for all hardware components, including pinouts, wiring diagrams, and electrical characteristics.

**Should contain:**
- **Component specifications**: Detailed specs for each hardware component
- **Pin assignments**: GPIO pin usage, motor controller connections
- **Wiring diagrams**: How components are connected
- **Power requirements**: Voltage, current, power budgeting
- **Mechanical specifications**: Dimensions, mounting points, ranges of motion

**Typical structure:**
```markdown
# Hardware Specifications

## System Overview
- Raspberry Pi 4B (main controller)
- PCA9685 servo controller (16-channel PWM)
- Roboclaw motor controllers (drive system)
- IMU sensor (orientation tracking)
- Camera system (vision processing)
- Battery and power distribution

## Pin Assignments

### Raspberry Pi GPIO Usage
| Pin | Function | Connected To |
|-----|----------|--------------|
| GPIO2 | I2C SDA | PCA9685, IMU |
| GPIO3 | I2C SCL | PCA9685, IMU |
| GPIO4 | PWM | Status LED |
| GPIO17 | Input | E-stop button |
| GPIO18 | PWM | Servo controller |

### Servo Controller (PCA9685)
- I2C address: 0x40
- Channels 0-4: Arm servos (base, shoulder, elbow, wrist, gripper)
- Channels 5-7: Reserved for expansion

### Motor Controllers (Roboclaw)
- Serial connection: /dev/ttyUSB0
- Address 128: Left drive motors
- Address 129: Right drive motors

## Power System
- Main battery: 7.4V LiPo, 5000mAh
- Servo power: 6V regulated
- Logic power: 3.3V/5V from Pi
- Current monitoring: Yes

## Mechanical Specifications
- Wheelbase: 300mm
- Ground clearance: 50mm
- Arm reach: 400mm horizontal, 300mm vertical
- Payload capacity: 500g
```

**Location:** `docs/hardware.md`

**When to use:**
- Hardware troubleshooting
- System modifications or expansions
- Understanding electrical characteristics
- Component replacement or repair

### **api.md** - API Reference Documentation
Complete API reference for all Python modules, classes, and functions. This is the technical reference for developers.

**Should contain:**
- **Module overviews**: What each module does
- **Class documentation**: Constructors, methods, properties
- **Function signatures**: Parameters, return types, exceptions
- **Example usage**: Code snippets showing how to use APIs
- **Inheritance diagrams**: Class relationships

**Typical structure:**
```markdown
# API Reference

## Core Modules

### robot.robot_system.RobotSystem
Main robot controller class.

#### Constructor
```python
RobotSystem(config_path="config/default.yaml")
```

#### Methods
- `initialize()` → bool: Initialize all subsystems
- `start()` → None: Start autonomous operation
- `stop()` → None: Stop all systems
- `get_status()` → dict: Get system status

#### Example
```python
robot = RobotSystem()
robot.initialize()
robot.start()

# Monitor status
while robot.is_running():
    status = robot.get_status()
    print(f"Battery: {status['battery']}%")
    time.sleep(1)
```

### arm.arm_controller.ArmController
Robotic arm control interface.

#### Key Methods
- `move_to_position(x, y, z)` → bool
- `open_gripper()` → None
- `close_gripper()` → None
- `get_position()` → tuple[float, float, float]

#### Exceptions
- `ArmKinematicsError`: Invalid position requested
- `ServoLimitError`: Joint limit exceeded
```

**Location:** `docs/api.md`

**When to use:**
- Writing new code that uses existing modules
- Understanding function parameters and return values
- Debugging API usage issues
- Extending or modifying existing functionality

### **troubleshooting.md** - Problem Diagnosis and Solutions
Comprehensive troubleshooting guide for common issues, organized by symptom and component.

**Should contain:**
- **Symptom-based diagnosis**: "Robot won't move" → check these things
- **Component-specific issues**: Drive system, arm, vision, sensors
- **Error message lookup**: What specific errors mean
- **Step-by-step debugging procedures**: Systematic problem isolation
- **Recovery procedures**: How to get back to working state

**Typical structure:**
```markdown
# Troubleshooting Guide

## System Won't Start

### Symptom: "ImportError: No module named 'cv2'"
**Cause:** OpenCV not installed
**Solution:**
```bash
pip install opencv-python
# Or for Raspberry Pi
sudo apt install python3-opencv
```

### Symptom: "Serial port not found"
**Cause:** Motor controllers not connected
**Check:**
1. USB cable connected: `lsusb | grep Roboclaw`
2. Serial port exists: `ls /dev/ttyUSB*`
3. Permissions: `sudo chmod 666 /dev/ttyUSB0`

## Robot Movement Issues

### Symptom: Robot moves erratically
**Possible causes:**
1. IMU calibration bad
2. PID gains too high
3. Encoder feedback noisy

**Debug steps:**
1. Check IMU: `python tools/test_sensors.py`
2. Tune PID: Adjust gains in `drive/pid.yaml`
3. Check encoders: `python tools/test_drive.py`

### Symptom: Robot doesn't move at all
**Check:**
1. Power to motor controllers
2. E-stop not engaged
3. Drive enable signals
4. Motor controller configuration

## Vision System Problems

### Symptom: No trash detection
**Debug sequence:**
1. Camera working: `python tools/camera_preview.py`
2. Model loaded: Check `models/trash_detector.pt` exists
3. Confidence threshold: May be too high (try 0.3)
4. Lighting conditions: Too dark/bright?

### Symptom: False detections
**Solutions:**
1. Lower confidence threshold
2. Filter by class (ignore non-trash)
3. Improve lighting
4. Retrain model with better data
```

**Location:** `docs/troubleshooting.md`

**When to use:**
- System not working as expected
- Error messages in logs
- Performance issues
- Hardware problems
- Unknown failures

## How to Use This Documentation

### **For New Developers**
1. Start with `docs/setup.md` - Get system running
2. Read `docs/hardware.md` - Understand the physical system
3. Use `docs/api.md` - Learn how to write code
4. Refer to `docs/troubleshooting.md` - When things go wrong

### **For Operators**
1. `docs/setup.md` - Initial setup
2. `docs/troubleshooting.md` - Fix problems
3. Individual module READMEs for specific components

### **For Maintainers**
1. `docs/hardware.md` - Hardware specifications
2. `docs/troubleshooting.md` - Diagnostic procedures
3. Module READMEs for detailed technical info

### **Debugging Workflow**
1. **Identify symptom** - What's not working?
2. **Check logs** - Look for error messages
3. **Consult troubleshooting** - Match symptom to solution
4. **Use API docs** - Understand correct usage
5. **Check hardware docs** - Verify connections
6. **Test step-by-step** - Isolate the problem

## Documentation Maintenance

### **Keeping Documentation Current**
- Update when code changes
- Add new troubleshooting cases as discovered
- Include hardware revisions
- Document configuration changes

### **Documentation Standards**
- Use consistent formatting
- Include code examples
- Provide cross-references
- Keep examples runnable
- Test instructions on fresh systems

### **Adding New Documentation**
- Follow existing structure
- Include table of contents
- Add cross-links between documents
- Update this README when adding files

## Common Documentation Issues

### Issue: Documentation out of date
**Symptoms:**
- Instructions don't work
- Code examples fail
- Missing new features

**Fix:**
- Compare docs with actual code
- Test all procedures
- Update for code changes
- Add version/change logs

### Issue: Missing troubleshooting cases
**When discovering new issues:**
1. Document the problem
2. Record the solution
3. Add to `troubleshooting.md`
4. Include debugging steps

### Issue: API docs incomplete
**For new code:**
1. Add docstrings to functions
2. Include parameter types and descriptions
3. Add usage examples
4. Document exceptions thrown

## Where to Find Everything

**Setup instructions:** `docs/setup.md`
- Follow for: New installations, hardware changes, recovery

**Hardware details:** `docs/hardware.md`
- Contains: Pinouts, specifications, wiring diagrams

**API reference:** `docs/api.md`
- Use for: Understanding function signatures, writing new code

**Troubleshooting:** `docs/troubleshooting.md`
- Use for: Error diagnosis, problem solving

**Project overview:** `../README.md`
- High-level project description and architecture

**Module details:** `../{module}/README.md`
- Detailed technical information for each subsystem

## Documentation Tools and Generation

### **Automatic API Documentation**
```bash
# Generate API docs from docstrings
pip install sphinx
sphinx-apidoc -f -o docs/api_source .
sphinx-build docs/api_source docs/api_html
```

### **Diagram Generation**
```bash
# Generate system architecture diagrams
pip install diagrams
python tools/generate_diagrams.py
```

### **Testing Documentation**
```bash
# Test setup instructions in clean environment
# Verify all code examples run
# Check all links work
```

## Contributing to Documentation

### **Documentation Standards**
- Write in clear, simple English
- Include working code examples
- Provide step-by-step instructions
- Test all procedures
- Keep consistent formatting

### **Review Process**
- Technical review by developers
- Testing by operators
- Updates for feedback
- Version control with changes

### **Documentation as Code**
- Documentation in same repository as code
- Versioned with code releases
- Reviewed in pull requests
- Tested in CI/CD pipeline
