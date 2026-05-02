# Teleoperation Module

This module provides remote control interfaces for manual operation of the Trashformer robot. It supports multiple input devices (gamepad, keyboard, joystick) and includes safety features, control mapping, and feedback systems for reliable human-robot interaction.

## Module Architecture Overview

```
Input Devices (gamepad, keyboard, joystick)
    ↓
Input Processing (dead zones, scaling, filtering)
    ↓
Command Generation (drive, arm, gripper commands)
    ↓
Safety Checks (limits, interlocks, E-stop)
    ↓
Robot Control (drive controller, arm controller)
```

## Files and Detailed Descriptions

### **gamepad_teleop.py** - Gamepad Controller Interface
Main teleoperation interface using gamepad controllers (Xbox, PlayStation, generic USB gamepads).

**Supported controllers:**
- **Xbox One/360 controllers**: Most common, well-tested
- **PlayStation 4/5 controllers**: Supported via USB
- **Generic USB gamepads**: Any SDL-compatible controller
- **Wireless adapters**: Bluetooth and proprietary wireless

**Key features:**
- **Analog control**: Smooth speed control with sticks
- **Button mapping**: Dedicated functions for common operations
- **Haptic feedback**: Vibration for status indication (if supported)
- **Hot-swappable**: Controller can be disconnected/reconnected

**Control mapping (Xbox controller):**
```
Left Stick Y-axis:  Forward/backward movement (-1 to +1)
Left Stick X-axis:  Strafe left/right (-1 to +1) [if supported]
Right Stick X-axis: Rotate left/right (-1 to +1)
Right Trigger:     Arm raise (+1)
Left Trigger:      Arm lower (-1)
A Button:          Gripper open
B Button:          Gripper close
X Button:          Pickup sequence (auto)
Y Button:          Emergency stop
Start Button:      Enable/disable control
Back Button:       Reset to home position
D-pad Up/Down:     Speed increase/decrease
Right Bumper:      Camera pan right
Left Bumper:       Camera pan left
```

**Usage example:**
```python
from teleop.gamepad_teleop import GamepadTeleop

# Initialize with configuration
teleop = GamepadTeleop(config=robot_config, simulate=False)

# Main control loop
while not teleop.should_exit():
    # Read controller state
    drive_cmd, arm_cmd, gripper_cmd = teleop.read_commands()
    
    # Apply safety checks
    if teleop.safety_ok():
        # Send commands to robot
        robot.drive.set_velocity(drive_cmd['linear'], drive_cmd['angular'])
        robot.arm.set_velocity(arm_cmd['shoulder'], arm_cmd['elbow'])
        robot.gripper.set_position(gripper_cmd['position'])
    
    # Small delay to prevent overwhelming controller
    time.sleep(0.02)  # 50 Hz update rate

teleop.cleanup()
```

**Location:** `teleop/gamepad_teleop.py` - `GamepadTeleop` class

**Configuration:**
```yaml
teleop:
  gamepad:
    deadzone: 0.1          # Ignore small stick movements
    max_linear_speed: 0.5  # m/s
    max_angular_speed: 1.0 # rad/s
    speed_increment: 0.1   # Speed change per button press
    controller_type: "xbox" # xbox, playstation, generic
```

### **keyboard_teleop.py** - Keyboard Control Interface
Simple keyboard-based control for development, testing, and fallback operation.

**Key mappings:**
```
Movement:
  W/↑:     Forward
  S/↓:     Backward  
  A/←:     Turn left
  D/→:     Turn right
  Q:       Strafe left (if supported)
  E:       Strafe right (if supported)

Arm Control:
  I:       Arm up/shoulder forward
  K:       Arm down/shoulder back
  J:       Elbow up
  L:       Elbow down
  U:       Wrist rotate left
  O:       Wrist rotate right

Gripper:
  Space:   Toggle gripper open/close
  G:       Gripper open
  H:       Gripper close

Special:
  1-9:     Predefined arm poses
  R:       Reset arm to home
  X:       Emergency stop
  C:       Clear errors
  V:       Toggle verbose mode
  ESC:     Exit teleop
```

**Usage:**
```python
from teleop.keyboard_teleop import KeyboardTeleop

teleop = KeyboardTeleop()
print("Keyboard teleop started. Use WASD for movement, ESC to exit.")

while True:
    # Non-blocking key check
    if teleop.key_pressed():
        cmd = teleop.get_command()
        
        if cmd['type'] == 'drive':
            robot.drive.set_velocity(cmd['linear'], cmd['angular'])
        elif cmd['type'] == 'arm':
            robot.arm.move_joint(cmd['joint'], cmd['velocity'])
        elif cmd['type'] == 'exit':
            break
    
    time.sleep(0.05)  # 20 Hz polling
```

**Location:** `teleop/keyboard_teleop.py` - `KeyboardTeleop` class

**Advantages:**
- **Always available**: No extra hardware needed
- **Precise control**: Individual key presses
- **Scriptable**: Can be automated for testing
- **Fallback**: Works when gamepad fails

### **arm_teleop.py** - Advanced Arm Teleoperation
Specialized interface for precise robotic arm control with multiple control modes.

**Control modes:**
1. **Joint control**: Direct control of individual joints
2. **Cartesian control**: Move end-effector in 3D space
3. **Pose control**: Select from predefined poses
4. **Teaching mode**: Record and playback movements

**Joint control mode:**
```python
# Direct joint velocity control
arm_cmd = {
    'mode': 'joint',
    'shoulder': 0.5,    # -1 to +1 (back/forward)
    'elbow': -0.2,      # -1 to +1 (down/up)
    'wrist': 0.0,       # -1 to +1 (rotation)
    'gripper': 1.0      # 0 (closed) to 1.0 (open)
}
```

**Cartesian control mode:**
```python
# End-effector position/velocity control
arm_cmd = {
    'mode': 'cartesian',
    'x': 0.1,           # Forward/back velocity (m/s)
    'y': 0.0,           # Left/right velocity (m/s)  
    'z': 0.05,          # Up/down velocity (m/s)
    'yaw': 0.0          # Rotation velocity (rad/s)
}
```

**Predefined poses:**
```python
# Move to named pose
poses = {
    'home': [0, 0, 0, 0],           # Stowed position
    'pickup': [0.3, 0.8, 0.2, 0.5], # Ready for pickup
    'drop': [0.5, 0.0, 0.8, 0.0],   # Above disposal area
    'inspect': [0.0, 0.5, 0.6, 0.8] # Camera inspection pose
}

robot.arm.move_to_pose(poses['pickup'])
```

**Location:** `teleop/arm_teleop.py` - `ArmTeleop` class

### **joystick_test.py** - Input Device Testing and Calibration
Utility for testing input devices, calibrating controls, and debugging input issues.

**Features:**
- **Device detection**: List all connected input devices
- **Live monitoring**: Display real-time input values
- **Calibration**: Set dead zones and sensitivity
- **Recording**: Save input sequences for testing
- **Visualization**: Plot input response curves

**Usage:**
```bash
# Test gamepad
python teleop/joystick_test.py --device gamepad

# Calibrate dead zones
python teleop/joystick_test.py --calibrate

# Record input sequence
python teleop/joystick_test.py --record output.json

# Playback recorded sequence
python teleop/joystick_test.py --playback input.json
```

**Location:** `teleop/joystick_test.py`

## Safety and Control Features

### **Safety Systems**
- **E-stop**: Immediate stop on dedicated button (Y on gamepad, X on keyboard)
- **Enable/disable**: Must press Start to enable control
- **Heartbeat monitoring**: Requires continuous operator input
- **Speed limiting**: Maximum speeds configurable and enforced
- **Joint limits**: Arm movements constrained to safe ranges
- **Obstacle detection**: Automatic stop if obstacles detected

### **Control Processing**
- **Dead zones**: Ignore small movements around center position
- **Scaling**: Map input ranges to appropriate velocity ranges
- **Filtering**: Smooth noisy input signals
- **Rate limiting**: Prevent excessively fast command changes
- **Mode switching**: Safe transitions between control modes

### **Feedback Systems**
- **Visual feedback**: Display current commands and status
- **Haptic feedback**: Controller vibration for warnings/errors
- **Audio cues**: Beeps for mode changes, errors
- **Status indicators**: LED lights showing system state

## Control Loop Architecture

### **Main Teleop Loop**
```python
class TeleopController:
    def __init__(self, robot, input_device):
        self.robot = robot
        self.input = input_device
        self.safety = SafetyMonitor()
        self.last_command_time = time.time()
        
    def run(self):
        while self.running:
            # 1. Read input
            raw_input = self.input.read()
            
            # 2. Process input (dead zones, scaling)
            processed_input = self.process_input(raw_input)
            
            # 3. Generate commands
            commands = self.generate_commands(processed_input)
            
            # 4. Safety checks
            if self.safety.check_commands(commands):
                # 5. Send to robot
                self.robot.execute_commands(commands)
                self.last_command_time = time.time()
            else:
                # Safety violation - stop robot
                self.robot.emergency_stop()
                
            # 6. Update operator feedback
            self.update_feedback()
            
            # 7. Maintain update rate
            time.sleep(0.02)  # 50 Hz
```

### **Input Processing Pipeline**
```
Raw Input → Dead Zone Filtering → Scaling → Rate Limiting → Command Generation
```

### **Command Validation**
```python
def validate_commands(self, commands):
    # Check velocity limits
    if abs(commands['drive']['linear']) > self.max_linear_speed:
        return False
        
    # Check joint limits
    for joint, pos in commands['arm'].items():
        if not self.joint_limits[joint].contains(pos):
            return False
            
    # Check safety interlocks
    if self.safety.emergency_active:
        return False
        
    return True
```

## Configuration and Tuning

### **Teleop Configuration**
```yaml
teleop:
  # General settings
  update_rate: 50          # Hz
  enable_safety: true
  heartbeat_timeout: 0.5   # seconds
  
  # Drive control
  drive:
    max_linear_speed: 0.5  # m/s
    max_angular_speed: 1.0 # rad/s
    deadzone: 0.1
    acceleration_limit: 1.0 # m/s²
    
  # Arm control
  arm:
    max_joint_speed: 1.0   # rad/s
    deadzone: 0.05
    cartesian_scaling: 0.1 # m/s per unit input
    
  # Gripper control
  gripper:
    open_position: 1.0
    closed_position: 0.0
    speed: 0.5
```

### **Device-Specific Calibration**
```yaml
gamepad_calibration:
  xbox:
    left_stick_deadzone: 0.1
    right_stick_deadzone: 0.1
    trigger_deadzone: 0.05
    axis_mapping: [0, 1, 3, 4]  # X, Y, RX, RY axes
    
  playstation:
    left_stick_deadzone: 0.08
    right_stick_deadzone: 0.08
    trigger_deadzone: 0.03
    axis_mapping: [0, 1, 2, 5]
```

## Common Issues and Debugging

### Issue: Controller not detected

**Symptoms:**
```
No gamepad found
pygame.error: No available video device
```

**Debug steps:**
```bash
# Check connected devices
ls /dev/input/js*
lsusb | grep -i gamepad

# Test with pygame
python -c "import pygame; pygame.init(); print(pygame.joystick.get_count())"

# Check permissions
ls -la /dev/input/js0
sudo chmod 666 /dev/input/js0

# Try different pygame backend
export SDL_VIDEODRIVER=dummy
```

**Fix:**
- Connect controller before starting program
- Use wired USB instead of Bluetooth
- Install correct drivers
- Run with sudo (temporary fix)

### Issue: Controls feel sluggish or unresponsive

**Symptoms:**
- Delayed response to input
- Jerky movement
- Controls not working at all

**Debug:**
```python
# Check update rate
start_time = time.time()
for i in range(100):
    cmd = teleop.read_commands()
end_time = time.time()
print(f"Update rate: {100/(end_time-start_time)} Hz")

# Check dead zone settings
print(f"Dead zone: {teleop.deadzone}")
print(f"Max speed: {teleop.max_speed}")

# Test raw input
raw = teleop.input.read_raw()
print(f"Raw input: {raw}")
```

**Fix:**
- Increase update rate in config
- Reduce dead zone if too large
- Check for blocking operations in loop
- Verify input device sampling rate

### Issue: Arm control not working properly

**Symptoms:**
- Arm moves in wrong direction
- Joint limits exceeded
- Cartesian control unstable

**Debug:**
```python
# Check joint directions
for joint in ['shoulder', 'elbow', 'wrist']:
    print(f"{joint} direction: {arm.joint_directions[joint]}")

# Verify joint limits
limits = arm.get_joint_limits()
print(f"Joint limits: {limits}")

# Test individual joint movement
arm.move_joint('shoulder', 0.1)  # Small test movement
time.sleep(1)
current_pos = arm.get_joint_position('shoulder')
print(f"Shoulder moved to: {current_pos}")
```

**Fix:**
- Correct joint direction signs in config
- Adjust joint limits to match hardware
- Tune PID gains for stable control
- Check kinematics calibration

### Issue: Emergency stop not working

**Symptoms:**
- E-stop button doesn't stop robot
- Robot continues moving after E-stop

**Debug:**
```python
# Check E-stop mapping
print(f"E-stop button: {teleop.estop_button}")
print(f"E-stop active: {teleop.estop_active}")

# Test E-stop circuit
robot.drive.emergency_stop()
time.sleep(0.1)
print(f"Drive stopped: {robot.drive.is_stopped()}")

# Check safety interlocks
print(f"Safety status: {robot.safety.get_status()}")
```

**Fix:**
- Verify button mapping in code
- Check E-stop wiring and connections
- Test motor controller E-stop input
- Ensure software E-stop takes precedence

### Issue: Control lag or latency

**Symptoms:**
- Noticeable delay between input and movement
- Jerky or stuttering control

**Debug:**
```python
# Measure end-to-end latency
start = time.time()
# Send command
teleop.send_command({'drive': {'linear': 0.1}})
# Wait for movement
while robot.drive.get_velocity() < 0.05:
    time.sleep(0.001)
end = time.time()
print(f"Latency: {(end-start)*1000} ms")

# Check system load
top -p $(pgrep -f teleop)

# Profile code performance
import cProfile
cProfile.run('teleop.run_one_cycle()')
```

**Fix:**
- Increase process priority: `chrt --rr 50 $(pgrep -f teleop)`
- Reduce update rate if system overloaded
- Optimize code (remove blocking operations)
- Use real-time kernel if available

## Advanced Features

### **Macro Recording and Playback**
```python
# Record a sequence
teleop.start_recording('my_macro')
# ... perform actions ...
teleop.stop_recording()

# Playback
teleop.playback_macro('my_macro', speed=0.5)
```

### **Force Feedback Control**
```python
# Provide haptic feedback
if robot.arm.is_stalled():
    gamepad.set_vibration(0.5, 0.5)  # Strong vibration
    time.sleep(0.2)
    gamepad.set_vibration(0, 0)      # Stop vibration
```

### **Multi-Device Control**
```python
# Use gamepad for drive, keyboard for arm
drive_teleop = GamepadTeleop()
arm_teleop = KeyboardTeleop()

while True:
    drive_cmd = drive_teleop.read_drive_command()
    arm_cmd = arm_teleop.read_arm_command()
    
    robot.drive.execute(drive_cmd)
    robot.arm.execute(arm_cmd)
```

## Testing and Validation

### **Teleop Testing Suite**
```bash
# Run automated tests
python -m pytest tests/test_teleop.py

# Test with simulated robot
python teleop/joystick_test.py --simulate

# Stress test control loop
python tools/stress_test_teleop.py --duration 300
```

### **Performance Benchmarks**
- **Latency**: <50ms end-to-end
- **Update rate**: 50-100 Hz
- **CPU usage**: <10% on Raspberry Pi 4
- **Memory usage**: <50MB

### **Safety Validation**
- E-stop response time: <100ms
- Command validation: All commands checked
- Heartbeat monitoring: 500ms timeout
- Joint limits: Hardware and software enforced

## Where to Find Everything

**Main teleop classes:** `teleop/*.py`
- `gamepad_teleop.py`: Gamepad control interface
- `keyboard_teleop.py`: Keyboard control interface
- `arm_teleop.py`: Advanced arm control
- `joystick_test.py`: Testing and calibration

**Configuration:** `config/hardware_config.yaml`
```yaml
teleop:
  gamepad:
    deadzone: 0.1
    max_speed: 0.5
  safety:
    enable_estop: true
    heartbeat_timeout: 0.5
```

**Logs:** `logs/trashformer_*.log` - Search for "teleop" or "gamepad"

**Test tools:** `tools/test_teleop.py` - Automated teleop testing

**Dependencies:** 
- `pygame`: Gamepad and joystick support
- `pynput`: Keyboard input (alternative)
- `inputs`: Linux input device access

## Development Notes

### **Adding New Input Devices**
1. Create new teleop class inheriting from base `TeleopInterface`
2. Implement `read_commands()` method
3. Add device-specific configuration
4. Update main teleop launcher

### **Custom Control Mappings**
```python
# Define custom mapping
custom_mapping = {
    'drive_forward': 'button_0',
    'drive_backward': 'axis_1_positive',
    'arm_up': 'button_3',
    'arm_down': 'button_2'
}

teleop.set_mapping(custom_mapping)
```

### **Networked Teleoperation**
```python
# Remote teleop over network
server = TeleopServer(port=8080)
server.start()

# Client sends commands
client = TeleopClient('robot.local', 8080)
client.send_command(drive_cmd)
```
- Inverse kinematics solver
- Collision avoidance
- Force feedback (if supported)

```python
from teleop.arm_teleop import ArmTeleop

arm_teleop = ArmTeleop()
# End-effector control
arm_teleop.move_end_effector(dx=0.1, dy=0, dz=0.05)
```

## Joystick Testing

Use the joystick test tool to:
- Detect connected input devices
- Calibrate analog sticks
- Test button mapping
- Verify force feedback

```bash
python teleop/joystick_test.py
```

## Features

- Multiple device support (hot-swap)
- Deadzone filtering for stick drift
- Acceleration ramps to prevent jerky motion
- Safety limits on command values
- Failsafe on connection loss
- Response time optimization

## Control Modes

### Direct Mode
Raw input directly to motors (testing only)

### Velocity Mode
Input specifies desired velocity (safe)

### Pose Mode
Input selects predefined robot poses

### Assisted Mode
User provides high-level commands (move toward target)

## Safety in Teleoperation

Safety features include:
- Speed limiting
- Acceleration limiting
- Timeout detection (stop on input loss)
- Emergency stop integration
- Operator feedback (status display)

## Configuration

Teleoperation parameters in:
- `../config/default.yaml` - Control sensitivity, dead zones
- Hardware specific mappings - Button/stick assignments

## Latency Considerations

Network teleoperation adds latency:
- Minimize network delay (wired Ethernet preferred)
- Implement predictive motion for smooth feedback
- Use local logging for troubleshooting
- Consider operator experience with latency

## Example: Custom Gamepad Mapping

```python
from teleop.gamepad_teleop import GamepadTeleop

teleop = GamepadTeleop()
# Override default mapping
teleop.set_mapping('LT', 'arm_forward')
teleop.set_mapping('RT', 'arm_backward')
```
