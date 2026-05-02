# Data Directory

This directory contains all persistent data for the Trashformer robot system, including calibration parameters, runtime logs, and configuration backups. This data is critical for proper robot operation and is loaded at system startup.

## Directory Structure

```
data/
├── calibration/          # Calibration data (critical for operation)
│   ├── camera_params.json    # Camera intrinsic/extrinsic parameters
│   ├── imu_offsets.json      # IMU sensor calibration
│   └── servo_limits.json     # Servo motor limits and specs
├── logs/                 # Runtime logs (created at runtime)
└── backups/              # Configuration backups (optional)
```

## Calibration Data - Detailed Explanations

### **camera_params.json** - Camera Calibration Parameters
Contains all camera calibration data needed to convert pixel coordinates to real-world coordinates. This is essential for the vision system to accurately position the arm for trash pickup.

**File structure:**
```json
{
  "camera_matrix": [
    [fx, 0, cx],
    [0, fy, cy],
    [0, 0, 1]
  ],
  "distortion_coefficients": [k1, k2, p1, p2, k3],
  "image_width": 640,
  "image_height": 480,
  "camera_to_robot_transform": [
    [r11, r12, r13, tx],
    [r21, r22, r23, ty],
    [r31, r32, r33, tz],
    [0, 0, 0, 1]
  ],
  "calibration_date": "2024-01-15T10:30:00Z",
  "calibration_method": "chessboard",
  "reprojection_error": 0.5
}
```

**Parameters explained:**

**Camera Matrix (Intrinsic parameters):**
- `fx, fy`: Focal length in pixels (how much zoom the lens has)
- `cx, cy`: Principal point (optical center, usually image center)
- Used to convert from camera coordinates to pixel coordinates

**Distortion Coefficients:**
- `k1, k2, k3`: Radial distortion (barrel/pincushion effect)
- `p1, p2`: Tangential distortion (lens not perfectly aligned)
- Corrects lens imperfections for accurate measurements

**Camera-to-Robot Transform (Extrinsic parameters):**
- 4×4 transformation matrix
- Rotation (r11-r33): Camera orientation relative to robot
- Translation (tx, ty, tz): Camera position relative to robot center
- Converts camera coordinates to robot body coordinates

**Usage in code:**
```python
import json
import cv2
import numpy as np

# Load calibration
with open('data/calibration/camera_params.json', 'r') as f:
    calib = json.load(f)

# Create camera matrix for OpenCV
camera_matrix = np.array(calib['camera_matrix'])
dist_coeffs = np.array(calib['distortion_coefficients'])

# Undistort image
undistorted = cv2.undistort(image, camera_matrix, dist_coeffs)

# Transform 3D point from camera to robot frame
camera_to_robot = np.array(calib['camera_to_robot_transform'])

# Point in camera coordinates
camera_point = np.array([x, y, z, 1])

# Transform to robot coordinates
robot_point = camera_to_robot @ camera_point
```

**Location:** `data/calibration/camera_params.json`

**How it's generated:**
```bash
# Use camera calibration tool
python tools/camera_preview.py --calibrate

# Or manual calibration with chessboard
python tools/camera_preview.py --chessboard
```

**Debugging camera calibration:**
- **Poor accuracy**: Check chessboard is flat and well-lit
- **High reprojection error**: Take more calibration images (20-50 recommended)
- **Wrong transform**: Measure camera position manually and verify

### **imu_offsets.json** - IMU Sensor Calibration
Contains calibration data for the Inertial Measurement Unit (IMU) sensor, which measures acceleration, rotation rate, and magnetic field. Proper calibration is crucial for accurate robot orientation and navigation.

**File structure:**
```json
{
  "accelerometer": {
    "offset": [ax_offset, ay_offset, az_offset],
    "scale": [ax_scale, ay_scale, az_scale],
    "bias_stability": 0.01
  },
  "gyroscope": {
    "offset": [gx_offset, gy_offset, gz_offset],
    "scale": [gx_scale, gy_scale, gz_scale],
    "bias_drift": 0.001
  },
  "magnetometer": {
    "offset": [mx_offset, my_offset, mz_offset],
    "scale": [mx_scale, my_scale, mz_scale],
    "hard_iron": [hx, hy, hz],
    "soft_iron": [[s11, s12, s13],
                  [s21, s22, s23],
                  [s31, s32, s33]]
  },
  "temperature_compensation": {
    "temp_offset": 25.0,
    "accel_temp_coeff": [0.01, 0.01, 0.01],
    "gyro_temp_coeff": [0.001, 0.001, 0.001]
  },
  "calibration_date": "2024-01-15T11:00:00Z",
  "calibration_method": "6-position",
  "accuracy_grade": "navigation"
}
```

**Parameters explained:**

**Accelerometer calibration:**
- **Offset**: Zero-point correction (what sensor reads when stationary)
- **Scale**: Sensitivity correction (converts raw units to m/s²)
- **Bias stability**: How much zero-point drifts over time

**Gyroscope calibration:**
- **Offset**: Zero-rate correction (what sensor reads when not rotating)
- **Scale**: Sensitivity correction (converts raw units to rad/s)
- **Bias drift**: How much zero-point changes with temperature/time

**Magnetometer calibration:**
- **Offset/Scale**: Correct hard and soft iron distortions
- **Hard iron**: Constant magnetic field distortion (from robot metal)
- **Soft iron**: Scale/shear distortion (from robot shape)

**Temperature compensation:**
- Corrects for sensor changes with temperature
- Critical for long-running robots

**Usage in code:**
```python
# Load IMU calibration
with open('data/calibration/imu_offsets.json', 'r') as f:
    imu_calib = json.load(f)

# Correct raw accelerometer reading
raw_accel = sensor.get_accelerometer()  # [ax, ay, az]
corrected_accel = (raw_accel - imu_calib['accelerometer']['offset']) * imu_calib['accelerometer']['scale']

# Corrected accel now in m/s²
print(f"Acceleration: {corrected_accel} m/s²")
```

**Location:** `data/calibration/imu_offsets.json`

**How it's generated:**
```bash
# IMU calibration procedure
python tools/calibrate_imu.py

# Requires:
# 1. 6-position calibration (robot placed in different orientations)
# 2. Figure-8 motion for magnetometer
# 3. Temperature variation testing
```

**Debugging IMU calibration:**
- **Drifting heading**: Poor magnetometer calibration
- **Inconsistent acceleration**: Accelerometer bias not stable
- **Temperature sensitivity**: Missing temperature compensation

### **servo_limits.json** - Servo Motor Specifications
Contains physical limits and specifications for all servo motors in the robotic arm. This prevents damage from over-driving motors and ensures safe operation.

**File structure:**
```json
{
  "servos": {
    "base": {
      "id": 0,
      "min_angle": -90,
      "max_angle": 90,
      "home_angle": 0,
      "max_speed": 100,
      "max_torque": 80,
      "direction": 1,
      "offset": 0
    },
    "shoulder": {
      "id": 1,
      "min_angle": -45,
      "max_angle": 135,
      "home_angle": 90,
      "max_speed": 80,
      "max_torque": 90,
      "direction": -1,
      "offset": 5
    },
    "elbow": {
      "id": 2,
      "min_angle": 0,
      "max_angle": 180,
      "home_angle": 90,
      "max_speed": 120,
      "max_torque": 70,
      "direction": 1,
      "offset": -2
    },
    "wrist": {
      "id": 3,
      "min_angle": -90,
      "max_angle": 90,
      "home_angle": 0,
      "max_speed": 150,
      "max_torque": 50,
      "direction": 1,
      "offset": 0
    },
    "gripper": {
      "id": 4,
      "min_angle": 0,
      "max_angle": 60,
      "home_angle": 30,
      "max_speed": 200,
      "max_torque": 40,
      "direction": 1,
      "offset": 0
    }
  },
  "global_limits": {
    "max_voltage": 7.4,
    "min_voltage": 6.0,
    "temperature_limit": 70,
    "current_limit": 2.0
  },
  "calibration_date": "2024-01-15T09:00:00Z"
}
```

**Parameters explained:**

**Per-servo settings:**
- **min_angle/max_angle**: Mechanical limits (degrees) - never exceed!
- **home_angle**: Neutral/safe position
- **max_speed**: Maximum rotation speed (deg/s)
- **max_torque**: Maximum torque limit (% of rated)
- **direction**: 1 or -1 (servo mounting direction)
- **offset**: Angle offset correction (degrees)

**Global limits:**
- **Voltage range**: Safe operating voltage
- **Temperature limit**: Maximum allowed temperature
- **Current limit**: Maximum current draw

**Usage in code:**
```python
# Load servo limits
with open('data/calibration/servo_limits.json', 'r') as f:
    servo_limits = json.load(f)

# Check if move is safe
def is_safe_move(servo_name, target_angle):
    limits = servo_limits['servos'][servo_name]
    return limits['min_angle'] <= target_angle <= limits['max_angle']

# Apply direction and offset corrections
def correct_angle(servo_name, raw_angle):
    limits = servo_limits['servos'][servo_name]
    corrected = raw_angle * limits['direction'] + limits['offset']
    return corrected
```

**Location:** `data/calibration/servo_limits.json`

**How it's generated:**
```bash
# Servo calibration procedure
python tools/calibrate_servos.py

# Process:
# 1. Find mechanical limits (move until stall)
# 2. Set home positions
# 3. Measure direction and offsets
# 4. Test speed/torque limits
```

## Runtime Data (logs/)

**Log files created during operation:**
- `trashformer_YYYYMMDD_HHMMSS.log` - Main system log
- `vision_debug.log` - Vision system details
- `arm_kinematics.log` - Arm movement logs
- `drive_control.log` - Drive system logs

**Log levels:**
- **DEBUG**: Detailed internal state (for development)
- **INFO**: Normal operation events
- **WARNING**: Potential issues
- **ERROR**: Serious problems
- **CRITICAL**: System-threatening failures

**Log rotation:**
- Files automatically rotate when they reach 10MB
- Keep last 7 days of logs
- Compress old logs to save space

## Data Management Best Practices

### **Backup Strategy**
```bash
# Backup calibration data
cp -r data/calibration data/calibration_backup_$(date +%Y%m%d)

# Backup configuration
cp config/*.yaml config/backup_$(date +%Y%m%d)/
```

### **Version Control**
- **DO commit**: Default configurations, empty calibration templates
- **DO NOT commit**: Actual calibration data (machine-specific)
- **DO NOT commit**: Logs, temporary files

### **Data Integrity**
- Validate JSON syntax before loading
- Check calibration dates are recent
- Verify checksums for critical data
- Backup before overwriting calibration

## Common Issues and Debugging

### Issue: Camera calibration data corrupted/missing

**Symptoms:**
- Vision system can't position arm correctly
- "Calibration file not found" errors
- Pickups consistently miss targets

**Debugging:**
```bash
# Check file exists and is valid JSON
ls -la data/calibration/camera_params.json
python -c "import json; json.load(open('data/calibration/camera_params.json'))"

# Regenerate calibration
python tools/camera_preview.py --calibrate
```

**Prevention:**
- Backup calibration before system updates
- Check calibration date is recent
- Validate reprojection error < 1.0 pixels

### Issue: IMU calibration drifting over time

**Symptoms:**
- Robot heading becomes inaccurate
- Navigation errors accumulate
- IMU readings don't match reality

**Debugging:**
```python
# Check calibration age
import json
calib = json.load(open('data/calibration/imu_offsets.json'))
print(f"Calibration date: {calib['calibration_date']}")

# Test static readings (should be ~[0,0,9.81] m/s²)
accel_readings = []
for i in range(100):
    accel_readings.append(sensor.get_accelerometer())
avg_accel = np.mean(accel_readings, axis=0)
print(f"Average acceleration: {avg_accel}")
```

**Fix:**
```bash
# Recalibrate IMU
python tools/calibrate_imu.py
```

### Issue: Servo limits causing crashes

**Symptoms:**
- Servo motors stalling and overheating
- "Angle out of range" errors
- Mechanical damage to robot

**Debugging:**
```python
# Check current servo positions
for servo_name, servo in arm.servos.items():
    current_angle = servo.get_position()
    limits = servo_limits['servos'][servo_name]
    print(f"{servo_name}: {current_angle}° (limits: {limits['min_angle']}° to {limits['max_angle']}°)")

# Test servo movement
python tools/test_servos.py
```

**Prevention:**
- Always check limits before commanding movement
- Use software limits in addition to mechanical stops
- Monitor servo temperature and current

### Issue: Log files growing too large

**Symptoms:**
- Disk space running low
- System slowdown from logging
- Old logs not being cleaned up

**Fix:**
```bash
# Check log sizes
du -sh logs/*.log

# Manual cleanup
find logs/ -name "*.log" -size +10M -delete

# Configure log rotation in config
logging:
  max_file_size: "10MB"
  backup_count: 5
  max_age_days: 7
```

### Issue: Calibration data format errors

**Symptoms:**
- JSON parsing errors at startup
- "KeyError" exceptions
- System fails to initialize

**Debugging:**
```python
# Validate all calibration files
import json
import os

calib_files = [
    'data/calibration/camera_params.json',
    'data/calibration/imu_offsets.json', 
    'data/calibration/servo_limits.json'
]

for file_path in calib_files:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"✓ {file_path}: Valid JSON")
        
        # Check required keys exist
        if 'calibration_date' not in data:
            print(f"⚠ {file_path}: Missing calibration_date")
            
    except json.JSONDecodeError as e:
        print(f"✗ {file_path}: Invalid JSON - {e}")
    except FileNotFoundError:
        print(f"✗ {file_path}: File not found")
```

## Where to Find Everything

**Camera calibration:** `data/calibration/camera_params.json`
- Used by: `vision/camera.py`, `vision/detector.py`
- Generated by: `tools/camera_preview.py --calibrate`

**IMU calibration:** `data/calibration/imu_offsets.json`
- Used by: `sensors/imu.py`, `sensors/sensor_fusion.py`
- Generated by: `tools/calibrate_imu.py`

**Servo limits:** `data/calibration/servo_limits.json`
- Used by: `arm/arm_controller.py`, `arm/servo.py`
- Generated by: `tools/calibrate_servos.py`

**Log files:** `logs/trashformer_*.log`
- Written by: All modules via `utils/logger.py`
- Viewed with: `tail -f logs/trashformer.log`

**Backup location:** `data/backups/` (create if needed)

## Data Flow and Dependencies

**Calibration loading sequence:**
1. System startup
2. Load `config/default.yaml` (base config)
3. Load `config/hardware_config.yaml` (hardware specifics)
4. Load calibration data from `data/calibration/`
5. Initialize subsystems with calibrated parameters
6. Start logging to `logs/`

**Critical dependencies:**
- Vision system requires camera calibration
- Navigation requires IMU calibration
- Arm control requires servo limits
- All systems require valid configuration

**Failure handling:**
- Missing calibration → Use safe defaults + warning
- Corrupted data → System halt with error message
- Old calibration → Warning but continue operation
