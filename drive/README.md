# Drive Module

This module handles locomotion by controlling the main drive motors (wheels), reading wheel encoders for odometry, and implementing PID speed control for accurate movement. The drive system is the primary way the robot navigates its environment and positions itself for trash pickup operations.

## Module Architecture

```
DriveController (high-level commands)
    ├─ RoboclawController or SabertoothController (motor hardware)
    ├─ Encoders (wheel rotation tracking)
    ├─ PID (speed regulation)
    └─ Configuration (hardware setup)
```

## Files and Detailed Descriptions

### **drive_controller.py** - Main drive orchestration
The primary interface for robot movement:
- `DriveController` class managing overall drive state
- `set_velocity(linear, angular)` - Command robot speed (m/s and rad/s)
- Differential drive kinematics (converts velocity → left/right wheel speeds)
- Motor speed ramping (smooth acceleration)
- Odometry tracking (current position estimate)
- Battery voltage monitoring

**Key responsibilities:**
- Translates high-level velocity commands into individual motor commands
- Manages motor controllers (Roboclaw, Sabertooth, etc.)
- Applies PID loop for accurate speed control
- Tracks robot position using encoder odometry
- Implements safety limits (max speed, acceleration)

**Location:** `drive/drive_controller.py` - Main `DriveController` class around line 1-50

**Important variables to understand:**
- `linear_velocity` - Forward/backward speed (m/s, positive = forward)
- `angular_velocity` - Rotation rate (rad/s, positive = counterclockwise)
- `left_wheel_speed` and `right_wheel_speed` - Individual motor speeds (RPM or encoder ticks/sec)
- Odometry state: `x, y, theta` (robot position and heading)

### **roboclaw_controller.py** - Roboclaw motor driver
Interface to Roboclaw dual motor controller (common choice for large robots):
- Serial communication with Roboclaw hardware via USB/RS232
- Command motor velocity or PWM
- Read motor current and speed feedback
- Battery voltage reading
- Error status and diagnostic info

**Roboclaw specifics:**
- Communicates at 115200 baud (configurable)
- Uses CRC checksums for reliability
- Each Roboclaw controls 2 independent motors
- Can chain multiple Roboclaws for more motors
- Provides current sensing (useful for stall detection)

**Configuration location:** `config/hardware_config.yaml` under `drive.roboclaw`
```yaml
drive:
  roboclaw:
    port: "/dev/ttyUSB0"  # Serial port path
    baudrate: 115200
    address: 128  # Device address (configurable on hardware)
    left_motor: 1  # Motor M1 or M2
    right_motor: 2
```

**Location:** `drive/roboclaw_controller.py` - Look for class `RoboclawController`

### **sabertooth_serial.py** - Sabertooth motor driver
Alternative motor controller interface (simpler, lower cost):
- Serial communication (typically 9600 baud)
- Two motor channels (M1, M2)
- PWM-style speed commands (-127 to +127)
- Status queries

**Sabertooth specifics:**
- Simpler command protocol than Roboclaw
- No current feedback (safety concern - can't detect stalls)
- Good for smaller systems
- Requires dip-switch configuration on hardware

**Configuration location:** `config/hardware_config.yaml` under `drive.sabertooth`
```yaml
drive:
  sabertooth:
    port: "/dev/ttyUSB1"
    baudrate: 9600
```

**Location:** `drive/sabertooth_serial.py` - Look for class `SabertoothController`

### **encoders.py** - Wheel rotation tracking
Reads quadrature encoders on motor shafts or wheel hubs:
- `Encoder` class for each wheel
- Tick counting and velocity calculation
- Odometry integration (position from encoder difference)
- Encoder error detection (stuck encoder)

**How encoders work:**
1. Encoder generates pulse signals (two channels for quadrature, determine direction)
2. GPIO pins on main computer receive pulse edges
3. Each pulse represents small wheel rotation (typically 1 pulse = 0.5-5mm movement)
4. Module counts pulses to determine distance traveled
5. Comparing left vs right encoder ticks calculations turn angle

**Typical configuration:**
```yaml
encoders:
  left:
    pin_a: 27  # GPIO pin numbers (Raspberry Pi example)
    pin_b: 17
    ticks_per_rotation: 360  # Per motor shaft revolution
    wheel_diameter: 0.08  # Meters (8cm wheel)
  right:
    pin_a: 23
    pin_b: 24
    ticks_per_rotation: 360
    wheel_diameter: 0.08
```

**Location:** `drive/encoders.py` - `Encoder` class and `Odometry` class

**How to understand your encoder:**
- Examine motor shaft or wheel hub for encoder
- Count pulse lines (usually 20-360 per rotation)
- Measure wheel diameter (important for distance calculation!)
- This determines ticks_per_rotation and wheel_diameter in config

### **pid.py** - Speed regulation control
PID (Proportional-Integral-Derivative) loop for maintaining target speed:
- `PIDController` class (one per wheel)
- Reads actual speed (from encoders)
- Compares to target speed
- Adjusts PWM/voltage to motor
- Compensates for load variations

**PID tuning (critical for smooth driving):**
```python
pid = PIDController(
    kp=1.0,      # Proportional gain (how aggressively to correct)
    ki=0.1,      # Integral gain (accumulated error correction)
    kd=0.05      # Derivative gain (damping/smooth response)
)
```

- **Kp too high** → Oscillation/overshoot
- **Kp too low** → Slow response
- **Ki** → Eliminates steady-state error but can cause oscillation if too high
- **Kd** → Improves stability but sensitive to noise

**Configuration location:** `config/default.yaml` under `drive.pid`
```yaml
drive:
  pid:
    kp: 1.0
    ki: 0.1
    kd: 0.05
    max_integral: 50  # Anti-windup limit
```

**Location:** `drive/pid.py` - `PIDController` class

### **dual_roboclaw_setup.md** - Special documentation
Detailed setup guide for dual motor controller configuration:
- How to chain multiple Roboclaws
- Address configuration
- Wiring diagrams
- Diagnostic commands

**Location:** `drive/dual_roboclaw_setup.md` - Reference if using dual Roboclaw setup

## How Everything Works Together

### Movement Command Example

```python
drive.set_velocity(linear=0.5, angular=0.2)  # Move forward 50cm/s, turn left
```

**Step-by-step execution:**

1. **DriveController receives command** (linear=0.5 m/s, angular=0.2 rad/s)

2. **Convert to differential drive velocities**
   ```
   Wheelbase = 0.3 m (distance between left/right wheels)
   
   left_speed = linear - (wheelbase/2) * angular
   right_speed = linear + (wheelbase/2) * angular
   
   left_speed = 0.5 - 0.15 * 0.2 = 0.47 m/s
   right_speed = 0.5 + 0.15 * 0.2 = 0.53 m/s
   ```

3. **Convert velocities to target RPM**
   ```
   wheel_radius = 0.04 m (4cm wheel)
   wheel_circumference = 2π * 0.04 = 0.251 m
   
   left_rpm = (0.47 / 0.251) * 60 = 112 RPM
   right_rpm = (0.53 / 0.251) * 60 = 127 RPM
   ```

4. **PID control for each wheel**
   - Read actual encoder speed: left_actual = 110 RPM
   - Error = 112 - 110 = 2 RPM
   - Increase left motor PWM slightly via PID loop
   - Repeat every 50ms (20Hz control)

5. **Send commands to motor controller**
   - Roboclaw: `drive_motor(1, 2500)` (velocity in ticks/sec or PWM 0-32767)
   - Or Sabertooth: `drive_motor(1, 64)` (PWM 0-127)
   - Serial command sent to hardware via USB/RS232

6. **Motor controller updates motor**
   - Amplifies PWM signal to high current
   - Drives motor shaft (and wheel)
   - Motors spin, wheels turn

7. **Odometry updates position**
   - Encoders measure wheel rotations
   - Left encoder ticks: 112 ticks/sec
   - Right encoder ticks: 127 ticks/sec
   - Calculate average: 119.5 ticks/sec
   - Conversion to distance: 0.49 m/s forward
   - Calculate rotation: (right - left) / wheelbase = 0.2 rad/s
   - Update robot position and heading in real-time

## Important Hardware Details

### Motor Controller Selection

**Roboclaw (RobotController, typical choice):**
- **Pros:** Dual channels, current sensing, robust
- **Cons:** More expensive, serial setup more complex
- **Use when:** Need stall detection or higher current demands
- **Port config:** `config/hardware_config.yaml` `drive.roboclaw.port`

**Sabertooth (simpler alternative):**
- **Pros:** Simple protocol, cheap
- **Cons:** No current feedback
- **Use when:** Simple 2-motor system without stall detection
- **Port config:** `config/hardware_config.yaml` `drive.sabertooth.port`

### Encoder Types

**Quadrature Encoders (most common):**
- Two signal channels (A and B)
- Phase difference indicates direction
- High resolution (360+ ticks per motor rotation)
- Needs GPIO pins on main computer

**Motor-integrated encoders:**
- Encoder on motor shaft (not wheel)
- Must multiply by gear ratio to get wheel distance
- Example: 360 ticks/motor rev, 10:1 gearbox = 3600 ticks/wheel rev

**Settings in config:**
- `ticks_per_rotation` - Encoder resolution (important!)
- `wheel_diameter` - Physical wheel size (also important!)
- Accuracy depends on both values

### Wheelbase

**Definition:** Distance between left and right wheels (front to back doesn't matter for differential drive)

**Impact on turning:**
- Used in differential drive kinematics
- Wrong value → turns too sharp or too gentle
- Located in: `config/hardware_config.yaml` under `drive.wheelbase`
- Measure both wheels' center lines, subtract

## Common Issues and Debugging

### Issue: Robot doesn't move when commanded

**Systematically check:**

1. **Motor power supply**
   ```bash
   # Check voltage at motor controller power input
   # Should match motor spec (12V, 24V, etc.)
   multimeter: Red to +V, Black to GND
   ```
   - Expected: 12V or 24V depending on system
   - If 0V: Power supply dead, wiring broken
   - If fluctuating: Power supply struggling, overload

2. **Motor controller connection**
   ```bash
   # List USB/serial devices
   ls /dev/ttyUSB*    # Linux
   # or check Device Manager on Windows
   ```
   - Should see at least one /dev/ttyUSB* device
   - If missing: USB driver not installed, cable bad
   - Test baud rate matches config: typically 115200 for Roboclaw, 9600 for Sabertooth

3. **Motor connections**
   - Check motor wires at controller terminals (not loose)
   - Swap left motor and right motor connections to see if they reverse roles
   - If other motor now works, first motor is wired incorrectly

4. **Serial communication test**
   ```python
   from drive.roboclaw_controller import RoboclawController
   rc = RoboclawController()
   try:
       status = rc.read_battery_voltage()
       print(f"Roboclaw connected, voltage: {status}")
   except Exception as e:
       print(f"Communication failed: {e}")
   ```
   - If error: Check USB port in config, try different USB port

5. **Encoder verification** (ensure encoders connected)
   ```python
   from drive.encoders import Encoder
   enc = Encoder(pin_a=27, pin_b=17)
   # Manually spin left wheel forward
   print(f"Left encoder count: {enc.get_ticks()}")
   # Should increase when spinning wheel forward
   ```

### Issue: Robot moves but direction is backwards

**Simple fix:**
1. Find which motor is reversed: Move forward, note which wheel goes backward
2. Physically swap motor wires at motor controller
3. Or swap motor channels in config and re-run
4. Test again

**Programmatic fix (if swapping wires isn't possible):**
- In `drive_controller.py` or motor controller, negate commands for that motor

### Issue: Robot drives fine straight but won't turn

**Diagnosis:**

1. **Wheelbase configuration wrong**
   - Robot turns radius too large or too small
   - Adjust `wheelbase` in `config/hardware_config.yaml`
   - Test: Command angular_velocity with zero linear
   - If circles too big: wheelbase is too large → decrease it
   - If circles too small: wheelbase too small → increase it

2. **Encoder ticks per rotation wrong**
   - Robot calculates wrong distance per tick
   - Results in incorrect odometry calculation
   - Physically rotate wheel one full rotation: should see exactly `ticks_per_rotation` ticks
   - If not: Recalibrate or fix encoder/gearbox ratio

3. **Wheel diameter wrong**
   - Similar effect as wrong ticks_per_rotation
   - Measure wheel diameter (tip to tip across center)
   - Example: 8cm wheel should be 0.08 in config

### Issue: Jerky or oscillating motion

**Causes:**

1. **PID gains too aggressive**
   - Symptom: Speed overshoots then corrects, oscillates
   - Fix: Reduce `kp` in `config/default.yaml` (try 0.5 instead of 1.0)
   - Or increase `kd` slightly for damping

2. **Control loop frequency too low**
   - Symptom: Very jerky movements
   - Fix: Increase `drive.control_rate_hz` in config (try 50Hz)
   - Requires more CPU

3. **Encoder resolution too low**
   - Symptom: Speed feedback very coarse
   - Fix: Can't change after hardware, but verify `ticks_per_rotation` is correct

4. **Speed ramping disabled or too fast**
   - Symptom: Jerky start/stop
   - Find `acceleration_limit` in config and reduce value (smoother ramp)

### Issue: Motor stalls or draws excessive current

**Safety concerns!**
This usually means mechanical problem or command too high.

**Debug:**
```python
# Read motor current if using Roboclaw
from drive.roboclaw_controller import RoboclawController
rc = RoboclawController()
current_ma = rc.read_motor_current(motor=1)
print(f"Motor 1 current: {current_ma}mA")
# Typically 0-5A normal, >10A is high
```

**Common causes:**
1. Wheel rubbing against frame (mechanical obstruction)
2. Motor gear damaged
3. Extremely high speed command → reduce max velocity
4. PID `kp` too high → reduce it
5. Battery voltage too low (motors work harder to produce same torque)

## Where to Find Key Configuration

**Main drive settings:** `config/hardware_config.yaml`
```yaml
drive:
  wheelbase: 0.3  # Distance between wheels (m)
  wheel_diameter: 0.08  # Wheel size (m)
  
  motor_type: "roboclaw"  # or "sabertooth"
  
  roboclaw:
    port: "/dev/ttyUSB0"
    baudrate: 115200
    left_motor: 1
    right_motor: 2
  
  encoders:
    left:
      pin_a: 27
      pin_b: 17
      ticks_per_rotation: 360
    right:
      pin_a: 23
      pin_b: 24
      ticks_per_rotation: 360
```

**PID tuning:** `config/default.yaml`
```yaml
drive:
  pid:
    kp: 1.0
    ki: 0.1
    kd: 0.05
    max_integral: 50
  
  max_velocity: 1.0  # m/s
  max_acceleration: 0.5  # m/s²
  control_rate_hz: 20
```

**Roboclaw setup (if needed):** `drive/dual_roboclaw_setup.md`

**Log files:** `logs/trashformer_*.log` - Search for "drive" or "encoder"

## Testing and Tool Usage

### Full drive test
```bash
python tools/test_drive.py
```
Tests:
- Motor connection and basic movement
- Each motor independently
- Forward/backward/turn commands
- Encoder reading
- PID control stability

###Testing Sabertooth motor controller
```bash
python tools/test_sabertooth.py
```
- Individual motor control
- Speed adjustment
- Bidirectional check

### Test sensors (including encoders)
```bash
python tools/test_sensors.py
```
- Encoder tick counting
- Odometry calculation
- Sensor update rates

## Performance Characteristics

**Typical values (system dependent):**
- Max speed: 0.5-2.0 m/s
- Max acceleration: 0.3-1.0 m/s²
- Control loop: 20-50 Hz
- Encoder feedback: 50-100 Hz
- Turning radius (depends on wheelbase): 0.5-2.0 meters

**Optimization:**
- Increase control rate for smoother motion (costs CPU)
- Tune PID gains for your specific motors and load
- Verify encoder configuration for accuracy
- Monitor battery voltage (low voltage reduces performance)

## Advanced Tuning

### PID Auto-tuning
If you want optimal PID gains:
```python
# Manual testing process:
# 1. Set ki=0, kd=0
# 2. Increase kp until oscillation just appears
# 3. Set kp to 2/3 of that value
# 4. Increase kd to dampen oscillation
# 5. Gradually add ki for steady-state correction
```

### Odometry Calibration
Over long distances, odometry drift accumulates:
```bash
python tools/calibrate_drive_odometry.py
# Drives in square, measures actual position
# Calculates correction factors
```

### Encoder Reliability
If encoders are noisy:
- Add software filtering: `from sensors.filtering import KalmanFilter`
- Verify GPIO cables aren't near power lines (EMI)
- Use shielded encoder cables
- Reduce control rate to filter out noise
