# Sensors Module

This module handles all robot sensor input including inertial measurement units (IMU), distance sensors (Time-of-Flight and ultrasonic), limit switches, sensor filtering, and multi-sensor fusion for robust state estimation. Understanding this module is critical for debugging robot navigation and positioning problems.

## Module Architecture Overview

```
Sensor Hardware (physical devices)
  ├─ IMU (I2C)
  ├─ TOF distance sensors (I2C)
  ├─ Ultrasonic sensors (GPIO)
  ├─ Limit switches (GPIO)
  └─ Wheel encoders (GPIO)
      ↓
Raw sensor interfaces (individual drivers)
  ├─ imu.py
  ├─ tof.py
  ├─ ultrasonic.py
  ├─ limit_switches.py
  └─ (encoders in drive module)
      ↓
Signal processing
  └─ filtering.py (Kalman, complementary filters)
      ↓
Sensor fusion
  └─ sensor_fusion.py (Combined state estimation)
      ↓
Robot state (Position, velocity, orientation)
```

## Files and Detailed Descriptions

### **imu.py** - Inertial Measurement Unit
6-axis motion sensor combining accelerometer and gyroscope:

**What it measures:**
- Accelerometer: Linear acceleration (m/s²) in X, Y, Z axes
  - Gravity always present (9.81 m/s² downward when stationary)
  - Tilt can be inferred from gravity direction
  - Bumps/collisions = large acceleration spikes

- Gyroscope: Rotational velocity (rad/s) around X, Y, Z axes
  - How fast robot is turning
  - Drifts over time (major issue - see calibration)
  - Very noisy in low-cost sensors

**Typical IMU chips (MPU6050, MPU9250, LSM6DS33):**
- Communication: I2C protocol
- I2C address: Usually 0x68 or 0x69 (configurable via AD0 pin)
- Update rate: 50-200 Hz possible (higher is better)
- Power: 3.3V (many support 5V with regulator)

**Usage example:**
```python
from sensors.imu import IMU

imu = IMU()
accel, gyro = imu.read()
print(f"Acceleration: {accel}")  # numpy array [x, y, z]
print(f"Rotation rate: {gyro}")   # numpy array [x, y, z]

# Typical values (robot on flat ground, no motion):
# accel: [0.1, -0.05, 9.81]  (small noise + gravity on Z)
# gyro:  [0.01, 0.02, -0.003]  (small noise/drift)
```

**Location:** `sensors/imu.py` - `IMU` class definition

**Configuration:**
```yaml
# config/hardware_config.yaml
sensors:
  imu:
    i2c_address: 0x68
    i2c_bus: 1  # /dev/i2c-1 on Linux
    update_rate_hz: 100
    range_accel_g: 16  # ±16g, or ±2, ±4, ±8
    range_gyro_deg_s: 2000  # ±2000°/s
```

### **tof.py** - Time-of-Flight Distance Sensor
Accurate infrared distance measurement (common: VL53L0X chip):

**How it works:**
1. Emits infrared light pulse
2. Light reflects off object
3. Measures time for reflection to return
4. Calculates distance: distance = time × speed_of_light / 2

**Characteristics:**
- Very accurate (±5% typical)
- Fast update (50+ Hz)
- Short range (30cm-2m typical)
- Narrow beam (small field of view)
- Needs clear line-of-sight (works in sunlight)

**Multiple TOF sensors:**
Robot often has several TOF sensors:
- Front: Obstacle detection
- Sides: Wall following
- Bottom: Ground clearance
- Back: Reverse navigation

**Usage example:**
```python
from sensors.tof import TOFSensor

# Create sensor (must specify I2C address if multiple)
front_tof = TOFSensor(i2c_address=0x29)

# Read distance
distance_mm = front_tof.read_distance()
print(f"Distance: {distance_mm}mm = {distance_mm/1000}m")

# Typical values:
# - 100mm (10cm): Object close
# - 500mm (50cm): Good detection range  
# - 2000mm (2m): Far object
# - Out of range: >2000mm or <30mm
```

**Location:** `sensors/tof.py` - `TOFSensor` class

**Configuration:**
```yaml
sensors:
  tof:
    sensors:
      front:
        i2c_address: 0x29
        position: "front"
      left:
        i2c_address: 0x2A  # Different address = different sensor
        position: "left"
      right:
        i2c_address: 0x2B
        position: "right"
```

**Address configuration:**
- Each TOF sensor has fixed I2C address (e.g., 0x29 for VL53L0X)
- To use multiple: Need address modification circuit or multiplexer
- Or: Use time-sharing on single I2C line (less efficient)

### **ultrasonic.py** - Ultrasonic Distance Sensor
Budget-friendly distance measurement (common: HC-SR04):

**How it works:**
1. Sends ultrasonic (40kHz) sound pulse
2. Waits for reflection from object
3. Measures time delay = distance × 2 / speed_of_sound

**Characteristics:**
- Cheap (cheaper than TOF)
- Longer range (up to 4m)
- Wider beam (larger field of view)
- Slower update rate (10-20 Hz typical)
- Noisy (returns inconsistent values)
- Affected by temperature (speed of sound changes)
- Doesn't work well on soft/absorptive surfaces

**Wiring (HC-SR04):**
- Trig pin: GPIO output (triggers measurement)
- Echo pin: GPIO input (measures pulse width)
- GND, VCC: Power (5V)

**Usage example:**
```python
from sensors.ultrasonic import UltrasonicSensor

# rear_usonic = UltrasonicSensor(trig_pin=24, echo_pin=23)
distance_cm = rear_usonic.read_distance()
print(f"Distance: {distance_cm}cm")

# Typical values:
# - 10cm: Very close
# - 100cm: Detection range
# - 400cm: Far object
# - Values noisy, expect ±5-10cm error
```

**Location:** `sensors/ultrasonic.py` - `UltrasonicSensor` class

**Configuration:**
```yaml
sensors:
  ultrasonic:
    rear:
      trig_pin: 24
      echo_pin: 23
```

### **limit_switches.py** - Digital Input Switches
Simple on/off mechanical switches (e.g., gripper fully open/closed)

**Types:**
- Mechanical: Simple push button
- Micro-switch: Triggered by small lever
- Optical/magnetic: No mechanical contact

**Typical usage:**
- Gripper fully open: Signal indicates start position
- Gripper fully closed: Signal prevents overload
- Arm joint limits: Prevents mechanical damage
- Door/cover closed: Safety interlock

**Usage example:**
```python
from sensors.limit_switches import LimitSwitch

gripper_closed = LimitSwitch(pin=22, active_high=True)

if gripper_closed.is_triggered():
    print("Gripper is closed")
else:
    print("Gripper is open")

# Debouncing (hardware contact bounces)
if gripper_closed.is_triggered_stable(debounce_ms=20):
    # Confirmed switch is pressed (not just bounce)
```

**Location:** `sensors/limit_switches.py` - `LimitSwitch` class

**Wiring:**
- Normally open: GND when not pressed, floating when pressed
- Pull-up resistor (10kΩ) on signal line
- Signal goes to GPIO input pin

**Configuration:**
```yaml
sensors:
  limit_switches:
    gripper_closed:
      pin: 22
      active_high: false  # Pulled low when closed
    gripper_open:
      pin: 27
      active_high: false
```

### **filtering.py** - Signal Processing
Noise reduction and data smoothing:

**Kalman Filter:**
- Optimal linear filter for noisy measurements
- Predicts next state based on physics/motion model
- Combines prediction with new measurement
- Minimizes combined error
- Best for fusion of multiple sensors

```python
from sensors.filtering import KalmanFilter

# State: [position_x, position_y, velocity_x, velocity_y]
kf = KalmanFilter(
    state_dim=4,
    measurement_dim=2,  # Measure position only
    dt=0.05  # 50ms time-step (20Hz)
)

# Process noise: How much state can change between updates
kf.process_covariance[0:2, 0:2] *= 0.1  # Position can drift slightly

# Measurement noise: How much we trust measurements
kf.measurement_covariance[0:2, 0:2] *= 1.0  # Trust position readings

# Update with new measurement
position = [1.5, 2.0]  # From sensors
state = kf.update(position)
print(f"Filtered position: {state[0:2]}")  # Usually smoother than raw
```

**Complementary Filter:**
Simpler alternative for IMU fusion:
```python
from sensors.filtering import ComplementaryFilter

# Fuse accelerometer (noisy but accurate) with gyro (drifts)
cf = ComplementaryFilter(alpha=0.95)  # Trust accel 5%, gyro 95%

while True:
    accel = imu.get_acceleration()  # Noisy but no drift
    gyro = imu.get_rotation_rate()  # Less noisy but drifts
    
    # Attitude (roll, pitch, yaw)
    attitude = cf.update(accel, gyro, dt=0.01)
```

**Location:** `sensors/filtering.py` - `KalmanFilter`, `ComplementaryFilter` classes

### **sensor_fusion.py** - Multi-Sensor Integration
Combines multiple sensors for robust state estimation:

**State estimate includes:**
- Position (x, y)
- Velocity (vx, vy)
- Orientation (theta / yaw)
- Angular velocity (omega)

**Sensor contributions:**
- Wheel odometry: Good for forward motion, drifts on turns
- Gyroscope: Accurate rotation rate, no drift
- Accelerometer: Long-term gravity reference, noisy
- Distance sensors: Detect absolute distances to objects
- Vision: Detects known landmarks

**Fusion algorithm:**
1. Predict next state based on motion model and gyro
2. Add new odometry measurements (wheel ticks)
3. Add distance sensor measurements (obstacle vector)
4. Add vision measurements (landmark positions)
5. Outputs best estimate of current state

```python
from sensors.sensor_fusion import SensorFusion

fusion = SensorFusion()

# Provide different sensor readings (each optional)
fusion.add_imu_data(accel, gyro, timestamp)
fusion.add_odometry_data(left_wheel_speed, right_wheel_speed)
fusion.add_tof_data(front_distance, left_distance, right_distance)
fusion.add_vision_data(detected_landmarks)

# Get best current estimate
state = fusion.get_state()
print(f"Robot at: ({state.x:.2f}, {state.y:.2f})")
print(f"Heading: {state.theta:.1f}°")
print(f"Velocity: {state.vx:.2f} m/s")
```

**Location:** `sensors/sensor_fusion.py` - `SensorFusion` class

**How disagreement is detected:**
If odometry estimates position at X but vision says at X+1:
- High measurement noise detected
- One sensor marked as unreliable
- Other sensor weighted more heavily
- System continues to function (graceful degradation)

## Data Flow and Integration

**Typical sensor update cycle (20-50 Hz):**

```
1. Raw sensor reads (parallel threads)
   ├─ IMU I2C read (10ms)
   ├─ TOF I2C read (5ms)
   ├─ Encoder GPIO read (1ms)
   └─ Ultrasonic echo measure (50ms, slow!)

2. Individual sensor processing
   ├─ Unit conversion (raw values → physical units)
   ├─ Calibration offset application
   └─ Outlier rejection (throw away impossible values)

3. Filtering (smooth out noise)
   ├─ Kalman filter for each IMU axis
   └─ Moving average for slow sensors

4. Fusion (combine all sensors)
   ├─ Weighted average of conflicting signals
   ├─ Physics model prediction
   └─ State update

5. Output
   └─ Provide merged state to rest of system
```

## Understanding Sensor Coordinates

**Robot body frame:**
```
        Front (X+)
           ↑
           |
Left ← (+Y)|        → Right (-Y)
           |
       Rear (X-)
```

**IMU axes:**
- X-axis points forward
- Y-axis points left  
- Z-axis points up
- Rotation around Z = yaw (turning left/right)

**Distance sensor values in body frame:**
- Front TOF: Obstacle forward
- Left TOF: Obstacle to the left
- Right TOF: Obstacle to the right
- Rear ultrasonic: Obstacle backward

## Common Issues and Debugging

### Issue: IMU returning garbage or missing data

**What to check:**

1. **I2C connection**
   ```bash
   i2cdetect -y 1  # List all I2C devices
   # Should see "68" or "69" for MPU6050/MPU9250
   ```
   - If missing: Check wiring (SDA, SCL, GND, VCC)
   - Check pull-up resistors (4.7kΩ typical)
   - Try different I2C bus (i2cdetect -y 0)

2. **Power supply**
   - Measure voltage: Should be 3.3V on VCC pin
   - If 0V: Power line broken
   - If 5V: May damage sensor (check regulator)

3. **Address mismatch**
   ```python
   from sensors.imu import IMU
   imu = IMU(i2c_address=0x69)  # Try alternate address
   ```
   - Default is usually 0x68, but AD0 pin sets 0x69

4. **Calibration needed**
   ```bash
   python tools/calibrate_imu.py
   # Generates data/calibration/imu_offsets.json
   ```
   - Stores accelerometer and gyro biases
   - Improves accuracy significantly

### Issue: IMU data is drifting (orientation slowly changes)

**Root cause:** Gyroscope drift (inevitable in low-cost sensors)

**Visible symptoms:**
- Robot knows correct position but thinks it's rotated
- Heading estimate slowly diverges from ground truth
- Navigation curves in unexpected directions

**Solutions:**

1. **Increase gyroscope calibration offset**
   ```python
   # In calibrate_imu.py
   gyro_bias_x *= 1.1  # Increase correction factor
   ```

2. **Use accelerometer for heading correction**
   ```python
   # In sensor_fusion.py
   # Trust accel for long-term, gyro for short-term
   alpha = 0.98  # 98% gyro, 2% accel correction
   fused_heading = alpha * gyro_heading + (1-alpha) * accel_heading
   ```

3. **Reset heading periodically**
   - If you know robot is facing 0°, reset heading to 0
   - Prevents unbounded drift

### Issue: TOF sensor reading zero distance (out of range)

**Root causes:**

1. **Too close to object**
   - VL53L0X minimum range: ~30mm
   - Move object farther away
   - Or increase sensor range setting (less accurate)

2. **Too far from object**
   - Maximum range ~2000mm
   - Object is farther than sensor can measure
   - Sensor returns maximum value

3. **No reflective object**
   - Sensor pointing at black/absorptive surface
   - Or pointing at glass (infrared transparent)
   - Point at white/reflective surface for test

4. **I2C communication failure**
   ```python
   # Test I2C connection
   try:
       dist = tof_sensor.read_distance()
       print(f"Distance: {dist}mm")
   except Exception as e:
       print(f"I2C error: {e}")
   ```

### Issue: Ultrasonic sensor is very noisy/inconsistent

**Ultrasonic nature - these sensors are noisy!**

Typical solutions:

1. **Software filtering**
   ```python
   # Take multiple reads, use median
   distances = [usonic.read_distance() for _ in range(5)]
   median_distance = sorted(distances)[len(distances)//2]
   ```

2. **Temperature compensation**
   - Speed of sound changes with temperature
   - If sensor is compensated: Use config parameter for temp
   - Typical: -0.6 m/s per °C, from 340 m/s at 15°C

3. **Increase sample averaging**
   - In filtering.py, increase window size
   - More averaging = less noise but more delay

4. **Check for reflections**
   - Sound bounces off nearby walls
   - Can create phantom detections
   - Angle sensor to reduce reflections

### Issue: Limit switch not reliably triggering

**Common causes:**

1. **Contact bounce**
   ```python
   # Use debouncing
   if switch.is_triggered_stable(debounce_ms=50):
       # Wait 50ms to confirm, filters bounces
   ```

2. **Wiring issues**
   - Signal wire loose at GPIO pin
   - Pull-up resistor wrong value or missing
   - Long wire picking up noise

3. **Pin configuration wrong**
   ```python
   # Test reading raw GPIO
   import GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
   print(GPIO.input(22))  # Should be 1 when not pressed, 0 when pressed
   ```

4. **Mechanical misalignment**
   - Switch lever not actually being triggered
   - Physical mechanism needs adjustment

## Where to Find Key Configuration

**Sensor I2C addresses:** `config/hardware_config.yaml`
```yaml
sensors:
  imu:
    i2c_address: 0x68  # Or 0x69
    i2c_bus: 1
  tof:
    front:
      i2c_address: 0x29
    left:
      i2c_address: 0x2A
```

**GPIO pin assignments:** Same file
```yaml
sensors:
  encoders:
    left_pin_a: 27
    left_pin_b: 17
    right_pin_a: 23
    right_pin_b: 24
  limit_switches:
    gripper_closed: 22
    gripper_open: 27
  ultrasonic:
    rear_trig: 24
    rear_echo: 23
```

**Calibration data:** `data/calibration/imu_offsets.json`
```json
{
  "accel_offset": [0.1, -0.05, 0.2],
  "gyro_bias": [0.002, 0.001, -0.003],
  "mag_calibration": {...}
}
```

**Sensor filtering/fusion settings:** `config/default.yaml`
```yaml
sensors:
  fusion:
    method: "kalman"  # or "complementary"
    update_rate_hz: 20
  filtering:
    kalman_process_noise: 0.1
    kalman_measurement_noise: 1.0
```

**Log files:** `logs/trashformer_*.log` - Search for "sensor" to find issues

## Testing and Validation

### Quick sensor test
```bash
python tools/test_sensors.py
```
Shows real-time readings from all sensors

### IMU calibration
```bash
python tools/calibrate_imu.py
```
Generates optimal calibration offsets

### Individual sensor test
```python
# Test one specific sensor
from sensors.imu import IMU
imu = IMU()
for _ in range(10):
    accel, gyro = imu.read()
    print(f"Accel: {accel}, Gyro: {gyro}")
```

## Performance Characteristics

**Typical sensor update rates:**
- IMU: 100-200 Hz (fast, good resolution)
- TOF: 50-100 Hz (accurate)
- Ultrasonic: 10-20 Hz (very slow)
- Encoders: 50-100 Hz (sampling dependent)
- Limit switches: Event-driven (instant)

**Sensor accuracy:**
- IMU acc: ±0.1-0.5m/s² typical (with calibration)
- IMU gyro: ±0.5-5°/s typical (drifts)
- TOF distance: ±5% relative error
- Ultrasonic: ±5-10cm absolute error
- Encoders: ±1-5mm depending on wheel size

## Advanced Topics

### Sensor Fusion Tuning

For better state estimation:
1. Increase `process_noise` if sensors disagree (trust motion model less)
2. Decrease `measurement_noise` if sensors are accurate (trust measurements more)
3. Tune weights per sensor type:
   - Vision: low noise when landmark visible, high when lost
   - Odometry: low noise straight, high on turns (slippage)
   - IMU: very noisy accelerometer, cleaner gyro

### Custom Sensor Integration

To add new sensor (e.g., laser rangefinder):
1. Create new file: `sensors/laser.py`
2. Implement driver class
3. Add to sensor_fusion.py
4. Update configuration
5. Add testing tool
6. Update this README

### Handling Sensor Failures

Graceful degradation when sensor fails:
```python
try:
    imu_data = imu.read()
except SensorError:
    logger.warning("IMU offline, using dead reckoning only")
    # Continue without IMU data
```
