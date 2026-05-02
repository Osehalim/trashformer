# Arm Module

This module contains all code for controlling the robotic arm, including kinematics calculations, servo control, and trajectory planning. The arm module provides high-level control interfaces for moving the arm to specific poses or Cartesian coordinates, while internally managing the complex joint calculations and servo pulse-width modulation.

## Module Architecture Overview

The arm module follows a hierarchical control structure:

```
User Code
    ↓
ArmController (high-level commands)
    ↓
ArmKinematics (FK/IK calculations)
    ↓
Trajectory (motion planning)
    ↓
Servo (joint control)
    ↓
PCA9685Driver (PWM signals)
    ↓
Hardware (physical servos)
```

## Files and Detailed Descriptions

### **arm_controller.py** - Main orchestration layer
The primary interface for arm control. This file contains:
- `ArmController` class that manages the overall arm state
- Methods for moving to named poses (e.g., `move_to_pose("pickup")`)
- Cartesian coordinate-based movement (`move_to_cartesian()`)
- Joint angle direct control for testing
- Arm status queries (current position, moving state, error conditions)

**Key responsibilities:**
- Validates movement commands before execution
- Converts high-level goals into servo commands
- Manages arm state machine (idle, moving, error)
- Handles concurrent motion requests (queuing or interruption)

**Location:** `arm/arm_controller.py` lines 1-100+ depend on implementation

### **arm_kinematics.py** - Mathematical transforms
Contains the mathematical core for arm motion:
- `forward_kinematics()` - Convert 6 joint angles → end-effector (x, y, z, pitch, roll, yaw)
- `inverse_kinematics()` - Convert end-effector pose → 6 joint angles
- Jacobian matrix calculations for motion analysis
- Singularity detection (positions arm can't reach accurately)
- Reference frame transformations

**Mathematical details:**
- Uses Denavit-Hartenberg (DH) parameters defined in configuration
- FK is straightforward matrix multiplication of transformation matrices
- IK may have multiple solutions (different arm configurations reaching same point)
- Configurations selected based on current arm pose (minimizes joint movement)

**Location:** `arm/arm_kinematics.py` - Look for `class ArmKinematics` or functions starting with `compute_`

### **servo.py** - Joint-level control
Low-level servo communication layer:
- `Servo` class representing each joint
- PWM pulse width ↔ angle conversion
- Servo speed and acceleration control
- Error detection (servo not responding, overload)
- State feedback reading from servo

**How it works:**
- Each servo accepts pulse widths (usually 1000-2000 microseconds)
- Wider pulse = different angle depending on servo
- Module maintains calibration offsets per servo
- Monitors servo current to detect mechanical problems

**Location:** `arm/servo.py` - Main `Servo` class definition

### **pca9685_driver.py** - Hardware interface
Direct PWM controller driver for the PCA9685 chip connecting to servos:
- I2C communication with PCA9685 chip
- Frequency/frequency setup (typically 50Hz for servos)
- PWM pulse width generation for each channel (16 servo outputs available)
- Channel assignment to joints
- Fault detection if I2C communication fails

**Hardware connection:**
- PCA9685 connects via I2C (pins SDA, SCL)
- PCA9685 connects to power (GND, VCC)
- Output channels 0-15 → servo signal wires
- Reference configuration in: `config/hardware_config.yaml` under `arm.pca9685`

**Location:** `arm/pca9685_driver.py` - Look for I2C address 0x40 (default)

### **trajectory.py** - Motion planning
Smooth motion interpolation between start and goal positions:
- `Trajectory` class for time-based motion planning
- Trapezoidal velocity profiles (acceleration → constant speed → deceleration)
- Cubic Hermite spline interpolation for smooth paths
- Joint space vs. Cartesian space trajectory options
- Collision checking along trajectory (if enabled)

**How trajectories work:**
1. Define start pose, goal pose, duration
2. `trajectory.generate()` creates intermediate waypoints
3. Controller samples trajectory at fixed intervals (e.g., 50ms)
4. Produces smooth motion avoiding jerky movements
5. Respects velocity/acceleration limits

**Location:** `arm/trajectory.py` - `Trajectory` class and interpolation functions

### **calibration.py** - Servo setup utility
Calibration routines for establishing correct servo mappings:
- Interactive calibration of each joint angle
- Min/max angle limits discovery
- Neutral/home position setting
- Offset computation for consistent angle readback
- Calibration data persistence to `data/calibration/servo_limits.json`

**Calibration process:**
1. Manual positioning of arm to known angles (0°, 90°, 180°)
2. Record corresponding PWM values
3. Compute linear mapping between angle and PWM
4. Store offsets for runtime operation

**Location:** `arm/calibration.py` - `CalibrateArm` or similar class

### **poses.yaml** - Pose library
YAML file defining named arm poses:

```yaml
pickup:
  joint_angles: [0, 45, -90, 0, 45, 0]  # 6 joints
  duration: 2.0  # seconds to reach pose
  
home:
  joint_angles: [0, 0, 0, 0, 0, 0]
  duration: 1.5

place:
  joint_angles: [180, 30, -60, 0, 45, 180]
  duration: 2.5
```

**Location:** `arm/poses.yaml` - Can edit directly without restarting (reloaded on command)

## How Everything Works Together

### Movement to a Pose Example

```python
arm.move_to_pose("pickup")
```

**Behind the scenes:**
1. `arm_controller.move_to_pose()` looks up "pickup" in `poses.yaml`
2. Finds goal joint angles: [0, 45, -90, 0, 45, 0]
3. Gets current joint angles from servo feedback
4. Creates `Trajectory` from current → goal angles over 2.0 seconds
5. Samples trajectory every 50ms (20Hz control rate)
6. For each sample timestamp:
   - Gets intermediate joint angles from trajectory interpolation
   - Sends these angles to each `Servo` object
   - Each servo converts angle → PWM via calibration mapping
   - PWM values sent to `PCA9685Driver`
   - Driver sends I2C commands to PCA9685 hardware
   - PCA9685 generates PWM signals to servo motors
7. Waits until trajectory complete or movement interrupted

### Coordinate System Details

**Joint space (what we control directly):**
- 6 angles representing each motor position
- Example: [0°, 45°, -90°, 0°, 45°, 0°]
- What the servos move to

**Cartesian space (intuitive coordinates):**
- X, Y, Z position in meters/centimeters
- Plus orientation angles (pitch, roll, yaw)
- What the gripper ends up at in the world
- These must be converted to joint angles via IK

**Transformation pipeline:**
```
Cartesian goal (0.3m, 0.2m, 0.1m, 0°, 0°, 0°)
    ↓ [IK calculation]
Joint angles (θ1=10°, θ2=35°, θ3=-85°, θ4=5°, θ5=40°, θ6=0°)
    ↓ [Calibration mapping]
PWM values (ch0=1500µs, ch1=1625µs, ch2=1375µs, ...)
    ↓ [I2C to PCA9685]
PWM signals to 6 servos
```

## Common Issues and Debugging

### Issue: Arm doesn't move when commanded

**What to check:**
1. **Power supply** - Ensure servo power rail (often separate from control)
   - Check voltage: Should be 5-6V for most servos
   - Use multimeter: Ground pin vs. Red/Black wires
   - Look in: `config/hardware_config.yaml` under `power.arm_voltage`

2. **I2C communication with PCA9685**
   ```bash
   # List I2C devices
   i2cdetect -y 1  # (or bus 0 depending on platform)
   ```
   - Should see device at address 0x40 (PCA9685 default)
   - If missing: Check wiring, pull-up resistors, I2C enabled on system

3. **Check servo connections**
   - Signal wire (usually yellow) → PCA channel 0-5 (6 joints)
   - Ground wire → GND on PCA
   - Power wire → 5-6V supply (not PCA output!)
   - Look up pin assignments in: `config/hardware_config.yaml` under `arm.servo_pins`

4. **Check calibration data**
   - File: `data/calibration/servo_limits.json`
   - Should have 6 entries (one per joint)
   - Each entry: min_angle, max_angle, neutral_angle, offset
   - If file missing or wrong: Run `python tools/calibrate_servos.py`

5. **Enable debug logging**
   ```python
   from utils.logger import get_logger
   logger = get_logger('arm.arm_controller')
   logger.setLevel('DEBUG')  # See all operations
   ```

### Issue: Arm moves but angles are wrong

**Root causes and fixes:**
1. **Calibration offset incorrect**
   - Symptom: Moving to 0° goes to wrong angle
   - Fix: Recalibrate servo: `python tools/test_one_servo_pca.py --servo 0`
   - Manually position joint to 0° position, record PWM value
   - Update in `data/calibration/servo_limits.json`

2. **Joint reversal (moving backwards)**
   - Symptom: Move command triggers motion in wrong direction
   - Fix: In `poses.yaml` or calibration, negate all angle values for that joint
   - Or swap signal wire to another channel that's configured reversed

3. **Servo stalled (can't reach commanded angle)**
   - Symptom: Servo buzzes/vibrates but doesn't move
   - Causes: Mechanical jam, servos at torque limit, incorrect angle outside limits
   - Debug: 
     ```python
     current_angle = servo.read_angle()
     if abs(current_angle - target_angle) > 20:  # Degrees
         print("Servo didn't reach target, check for jamming")
     ```

### Issue: Jerky, non-smooth motion

**Solutions:**
1. **Trajectory sample rate too slow**
   - Increase control loop frequency in `config/default.yaml`
   - Change: `arm.control_rate_hz: 50` → `100` (higher is smoother)

2. **Velocity profile too aggressive**
   - Reduce maximum joint velocity: `arm.max_velocity_deg_per_sec: 180` → `90`
   - Increase trajectory duration in `poses.yaml`

3. **Servo update rate too slow**
   - Check I2C communication speed
   - Ensure PCA9685 refresh rate is high (typically 50Hz minimum)

### Issue: IK calculations fail or give weird results

**Debugging:**
```python
from arm.arm_kinematics import ArmKinematics

ik = ArmKinematics()

# Try to reach a position
goal_pose = [0.3, 0.2, 0.1, 0, 0, 0]  # x, y, z, roll, pitch, yaw
try:
    joint_angles = ik.inverse_kinematics(goal_pose)
    print(f"Solution found: {joint_angles}")
except Exception as e:
    print(f"IK failed: {e}")
    # This usually means position is unreachable
    # Try increasing Z (reaching higher) or reducing XY distance
```

**Common IK issues:**
1. **Singularity (arm configuration degenerate)**
   - At certain poses, multiple solutions or unstable solution
   - Solution: Slightly adjust goal position and try again

2. **Position unreachable**
   - Beyond arm's reach or below mounting point
   - Check: Maximum reach = sum of all link lengths
   - In config: `arm.kinematics.link_lengths: [...]`

3. **Wrong IK solution selected**
   - Several valid joint angle sets can reach same point
   - Algorithm selects one; may not be best
   - Workaround: Use pose library with pre-calculated angles

## Where to Find Key Configuration

**Main arm settings:** `config/hardware_config.yaml`
```yaml
arm:
  num_joints: 6
  servo_pins: [0, 1, 2, 3, 4, 5]  # PCA9685 channels
  pca9685_i2c_address: 0x40
  pca9685_i2c_bus: 1  # /dev/i2c-1 on Linux
  max_velocity_deg_per_sec: 180
  max_acceleration_deg_per_sec_sq: 360
```

**Servo limits and offsets:** `data/calibration/servo_limits.json`
```json
{
  "servo_0": {"min_angle": -90, "max_angle": 90, "neutral": 0, "pwm_offset": 1500},
  ...
}
```

**Pre-defined poses:** `arm/poses.yaml` (fully editable)

**Kinematic model:** Usually hardcoded in `arm_kinematics.py` or in `config/hardware_config.yaml` under `kinematics` section

**Log files:** `logs/trashformer_*.log` - Search for "arm" to find all arm-related messages

## Testing and Validation

### Quick arm test
```bash
python tools/test_arm_full.py
```
This will:
1. Move to each defined pose
2. Perform IK test to various positions
3. Check servo connectivity
4. Validate calibration data

### Individual servo test
```bash
python tools/test_one_servo_pca.py --servo 0 --pin 0
```
This tests servo on PCA9685 channel 0 in isolation

### Arm demo with visualization
```bash
python tools/demo_arm.py
```
Shows current arm state and allows interactive movement

## Performance Characteristics

**Typical values (adjust per system):**
- Move speed: 90-180°/second per joint
- Full reach extension: 1-2 seconds
- Control loop rate: 20-50 Hz
- IK computation time: 10-50ms
- Servo response lag: 50-100ms

**Optimization tips:**
- Reduce control rate if CPU limited (saves CPU but reduces smoothness)
- Cache IK solutions for common poses
- Use poses library instead of computing IK for repeated targets
- Batch servo commands in single I2C transaction if possible

## Advanced Topics

### Custom Kinematics
If implementing a different arm design:
1. Update link lengths in `config/hardware_config.yaml`
2. Modify DH parameters in `arm_kinematics.py`
3. Retest with known positions
4. Update pose library with new arm's angles

### Motion Planning with Obstacles
The trajectory module can check for collisions:
1. Define collision geometry (cylinder/sphere per link)
2. Pass environment obstacles to `trajectory.generate()`
3. Algorithm will avoid collisions in joint space
4. May fail if path impossible without collision

### Force Feedback (if supported)
Some servos report load/torque:
1. Read servo feedback in `servo.py`
2. Detect collisions if torque suddenly spikes
3. Implement compliance (reduce position setpoint if overload)
4. Integrate into `arm_controller.py` for automatic stall detection
