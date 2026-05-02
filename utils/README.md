# Utils Module

This module contains shared utility functions and helper classes that provide common functionality across all robot subsystems. These utilities handle configuration management, logging, mathematical operations, and communication protocols, ensuring consistent behavior and reducing code duplication throughout the system.

## Overview

The utils module serves as the foundation layer for the Trashformer robot system, providing:

- **Configuration Management**: Hierarchical YAML configuration loading with environment overrides
- **Logging System**: Centralized logging with file/console output and configurable levels
- **Mathematical Utilities**: Vector math, transformations, and kinematic calculations
- **Communication Utilities**: Serial port abstraction and protocol handling

All utilities are designed to be lightweight, thread-safe, and hardware-agnostic where possible.

## Directory Structure

```
utils/
├── __init__.py           # Module exports and initialization
├── config_loader.py      # YAML configuration management
├── logger.py             # Centralized logging system
├── math_helpers.py       # Mathematical utility functions
└── serial_utils.py       # Serial communication utilities
```

## Detailed Component Documentation

### Configuration Loader (config_loader.py)

**Purpose**: Robust YAML configuration file loading with hierarchical merging and environment variable substitution.

**What it does**:
- Loads multiple YAML files in priority order (default → hardware → environment)
- Performs deep merging of configuration dictionaries
- Substitutes environment variables in configuration values
- Validates configuration structure and types
- Caches loaded configurations for performance

**Technical Details**:
- Uses PyYAML for parsing with safe loading
- Implements recursive dictionary merging
- Supports environment variable syntax: `${VAR_NAME}` or `${VAR_NAME:default}`
- Validates required configuration keys
- Thread-safe configuration caching

**Core Functions**:

#### load_config(config_file=None, overrides=None)
**Parameters**:
- `config_file`: Specific config file to load (optional)
- `overrides`: Dictionary of configuration overrides (optional)

**Returns**: Merged configuration dictionary

**Usage**:
```python
from utils.config_loader import load_config

# Load default merged configuration
config = load_config()

# Load specific configuration file
dev_config = load_config('config/development.yaml')

# Load with runtime overrides
runtime_config = load_config(overrides={'drive.max_speed': 0.8})
```

**Configuration Hierarchy**:
1. `config/default.yaml` - Base configuration
2. `config/hardware_config.yaml` - Hardware-specific overrides
3. Environment-specific files (development.yaml, production.yaml)
4. Runtime overrides passed to load_config()

**Configuration File Format**:
```yaml
# config/default.yaml
robot:
  name: "Trashformer"
  version: "1.0.0"

drive:
  max_speed: 1.0
  acceleration: 0.5
  motor_controller: "sabertooth"

arm:
  servo_channels:
    shoulder: 0
    elbow: 1
    gripper: 2
  pwm_limits:
    min_pulse: 600
    max_pulse: 2400

logging:
  level: "INFO"
  file: "logs/trashformer.log"
  max_size: 10485760  # 10MB
```

**Debugging Configuration Issues**:
- **File not found**: Check file paths and permissions
- **YAML syntax error**: Use online YAML validator
- **Environment variables**: Verify variables are set before loading
- **Merge conflicts**: Check for conflicting keys in multiple files
- **Type errors**: Ensure values match expected types

**Files Used**:
- `config/default.yaml` - Base configuration
- `config/hardware_config.yaml` - Hardware overrides
- `config/development.yaml` - Development settings
- Environment variables for runtime configuration

### Logger (logger.py)

**Purpose**: Centralized logging system providing consistent logging across all robot components.

**What it does**:
- Creates module-specific loggers with hierarchical naming
- Configures file and console output handlers
- Implements log rotation and size limits
- Provides structured logging with timestamps and levels
- Supports different log formats for different outputs

**Technical Details**:
- Uses Python's built-in logging module
- Implements singleton pattern for logger configuration
- Thread-safe logging operations
- Configurable log levels per module
- Automatic log file rotation and cleanup

**Core Functions**:

#### setup_logging(config=None)
**Parameters**:
- `config`: Configuration dictionary (optional, loads from config if not provided)

**Usage**:
```python
from utils.logger import setup_logging
setup_logging()  # Uses configuration from config files
```

#### get_logger(name)
**Parameters**:
- `name`: Logger name (typically `__name__` for module-specific logging)

**Returns**: Configured logger instance

**Usage**:
```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.debug("Detailed debug information")
logger.info("General information message")
logger.warning("Warning about potential issue")
logger.error("Error that affects specific operations")
logger.critical("Critical error requiring immediate attention")
```

**Log Configuration**:
```yaml
# In config/default.yaml
logging:
  level: "INFO"           # Root log level
  file: "logs/trashformer.log"
  max_size: 10485760      # 10MB before rotation
  backup_count: 5         # Keep 5 backup files
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  console_level: "WARNING"  # Console shows WARNING and above
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic information for development
- `INFO`: General information about system operation
- `WARNING`: Potential issues that don't stop operation
- `ERROR`: Errors that affect specific operations
- `CRITICAL`: Critical errors requiring immediate attention

**Log Output Locations**:
- **Console**: Real-time output to terminal/command prompt
- **File**: Persistent logging to `logs/trashformer.log`
- **Rotation**: Automatic rotation when file reaches max_size

**Debugging Logging Issues**:
- **No logs appearing**: Check log level configuration
- **Permission denied**: Verify write access to logs directory
- **Large log files**: Check rotation settings and cleanup
- **Performance impact**: Use appropriate log levels in production

**Files Used**:
- `config/default.yaml` - Logging configuration
- `logs/trashformer.log` - Main log file
- `logs/trashformer.log.1` through `logs/trashformer.log.5` - Rotated logs

### Math Helpers (math_helpers.py)

**Purpose**: Mathematical utility functions for robot kinematics, sensor fusion, and motion control calculations.

**What it does**:
- Provides vector and matrix operations for 3D transformations
- Implements quaternion and Euler angle conversions
- Calculates distances, angles, and interpolation
- Handles numerical constraints and safety limits

**Technical Details**:
- Uses NumPy for efficient vectorized operations
- Implements numerically stable algorithms
- Handles edge cases and singularities
- Optimized for real-time robot control

**Core Functions**:

#### rotation_matrix(angle, axis)
**Parameters**:
- `angle`: Rotation angle in radians
- `axis`: Rotation axis ('x', 'y', 'z')

**Returns**: 3x3 rotation matrix

**Usage**:
```python
from utils.math_helpers import rotation_matrix
import numpy as np

# Rotate 45 degrees around Z axis
R_z = rotation_matrix(np.pi/4, 'z')
point = np.array([1.0, 0.0, 0.0])
rotated_point = R_z @ point
```

#### quaternion_to_euler(quaternion)
**Parameters**:
- `quaternion`: Quaternion as [w, x, y, z] or [x, y, z, w]

**Returns**: Euler angles (roll, pitch, yaw) in radians

#### euler_to_quaternion(roll, pitch, yaw)
**Parameters**:
- `roll`, `pitch`, `yaw`: Euler angles in radians

**Returns**: Quaternion as [w, x, y, z]

#### distance_2d(x1, y1, x2, y2)
**Parameters**:
- `x1`, `y1`: First point coordinates
- `x2`, `y2`: Second point coordinates

**Returns**: Euclidean distance between points

#### angle_difference(angle1, angle2)
**Parameters**:
- `angle1`, `angle2`: Angles in radians

**Returns**: Smallest difference between angles (-π to π)

#### clamp(value, min_val, max_val)
**Parameters**:
- `value`: Value to clamp
- `min_val`, `max_val`: Minimum and maximum bounds

**Returns**: Value constrained within bounds

#### linear_interpolation(start, end, alpha)
**Parameters**:
- `start`, `end`: Start and end values
- `alpha`: Interpolation factor (0.0 to 1.0)

**Returns**: Interpolated value

**Mathematical Operations**:
- **3D Transformations**: Rotation matrices, translation vectors, homogeneous transformations
- **Quaternion Math**: Multiplication, normalization, conjugation, slerp interpolation
- **Euler Angles**: 3-2-1 rotation sequence (ZYX), gimbal lock handling
- **Geometry**: Point-to-line distance, angle bisectors, polygon operations
- **Numerical Methods**: Root finding, optimization, constraint satisfaction
- **Filtering**: Moving averages, exponential smoothing, outlier detection

**Usage in Robot Systems**:
```python
# Arm kinematics
from utils.math_helpers import rotation_matrix, distance_3d

# Forward kinematics calculation
shoulder_rotation = rotation_matrix(shoulder_angle, 'z')
elbow_rotation = rotation_matrix(elbow_angle, 'y')
end_effector_pos = shoulder_rotation @ elbow_rotation @ arm_vector

# Sensor fusion
from utils.math_helpers import quaternion_to_euler

orientation = quaternion_to_euler(imu_quaternion)
robot_heading = orientation[2]  # Yaw angle
```

**Debugging Math Issues**:
- **Numerical instability**: Check for near-singular matrices
- **Unit mismatches**: Verify radians vs degrees, coordinate systems
- **Precision errors**: Use appropriate floating-point precision
- **Edge cases**: Test with boundary values and special cases

**Files Used**: Primarily computational, no external file dependencies.

### Serial Utilities (serial_utils.py)

**Purpose**: Abstraction layer for serial port communication with robot hardware devices.

**What it does**:
- Provides cross-platform serial port enumeration and connection
- Implements reliable read/write operations with timeouts
- Handles connection lifecycle and error recovery
- Supports different serial protocols and baud rates

**Technical Details**:
- Uses PySerial library for cross-platform compatibility
- Implements connection pooling and reuse
- Provides buffered I/O with configurable timeouts
- Handles serial port hot-plugging and disconnection

**Core Classes**:

#### SerialPort Class
**Initialization**:
```python
port = SerialPort(
    port='/dev/ttyUSB0',    # Serial port device
    baudrate=115200,        # Communication speed
    timeout=1.0,           # Read timeout in seconds
    write_timeout=1.0      # Write timeout in seconds
)
```

**Methods**:

##### write(data)
**Parameters**:
- `data`: Bytes to write to serial port

**Usage**:
```python
port.write(b'AT\r\n')
```

##### read(size)
**Parameters**:
- `size`: Number of bytes to read

**Returns**: Bytes read from port

##### read_until(delimiter, timeout=None)
**Parameters**:
- `delimiter`: Byte sequence to read until
- `timeout`: Override timeout for this read

**Returns**: Bytes read until delimiter

##### readline()
**Returns**: Single line terminated with `\n`

##### close()
Closes the serial connection and releases resources.

**Utility Functions**:

#### list_ports()
**Returns**: List of available serial ports

**Usage**:
```python
from utils.serial_utils import list_ports

available_ports = list_ports()
print("Available ports:", available_ports)
```

**Serial Configuration**:
- **Baud Rates**: 9600, 19200, 38400, 57600, 115200, 250000, 500000, 1000000
- **Data Bits**: 5, 6, 7, 8 (default: 8)
- **Stop Bits**: 1, 1.5, 2 (default: 1)
- **Parity**: None, Even, Odd, Mark, Space (default: None)
- **Flow Control**: None, RTS/CTS, XON/XOFF

**Error Handling**:
- **Connection failures**: Automatic retry with exponential backoff
- **Timeout handling**: Configurable timeouts with graceful degradation
- **Buffer overflows**: Automatic buffer management and clearing
- **Port disconnection**: Detection and reconnection logic

**Usage Patterns**:
```python
from utils.serial_utils import SerialPort
from utils.logger import get_logger

logger = get_logger(__name__)

def communicate_with_motor_controller():
    try:
        port = SerialPort('/dev/ttyUSB0', 115200)
        port.write(b'STATUS\r\n')
        response = port.read_until(b'\r\n', timeout=2.0)
        logger.info(f"Motor status: {response.decode().strip()}")
    except Exception as e:
        logger.error(f"Serial communication failed: {e}")
    finally:
        port.close()
```

**Debugging Serial Issues**:
- **Port not found**: Check device connections and permissions
- **Permission denied**: May need `sudo` or udev rules
- **Garbled data**: Verify baud rate and serial settings
- **Timeouts**: Check device response times and cable quality
- **Buffer issues**: Monitor for data overruns or underruns

**Files Used**: No external files, communicates directly with serial hardware.

## Integration Patterns

### Configuration + Logging Setup
```python
# Early system initialization
from utils.config_loader import load_config
from utils.logger import setup_logging

config = load_config()
setup_logging(config)

logger = get_logger(__name__)
logger.info("System initialized with config version {config['robot']['version']}")
```

### Math Operations in Control Loops
```python
from utils.math_helpers import clamp, angle_difference

def control_loop():
    # Read sensor data
    current_angle = imu.get_yaw()
    desired_angle = navigation.get_target_heading()

    # Calculate control error
    error = angle_difference(current_angle, desired_angle)

    # Apply PID control with clamped output
    control_signal = pid_controller.update(error)
    motor_command = clamp(control_signal, -1.0, 1.0)

    # Send to motors
    drive_system.set_speed(motor_command)
```

### Serial Communication with Devices
```python
from utils.serial_utils import SerialPort

class MotorController:
    def __init__(self, port, baudrate):
        self.port = SerialPort(port, baudrate)

    def set_speed(self, speed):
        command = f'M{speed:.2f}\r\n'.encode()
        self.port.write(command)
        response = self.port.read_until(b'\r\n')
        return response.decode().strip() == 'OK'
```

## Performance Characteristics

### Configuration Loading
- **First load**: ~50-100ms (parsing YAML, merging dictionaries)
- **Cached loads**: ~1-5ms (dictionary copy only)
- **Memory usage**: ~10-50KB for typical configurations

### Logging
- **Console logging**: ~0.1-1ms per message
- **File logging**: ~1-5ms per message (includes I/O)
- **Memory usage**: ~5-20KB per logger instance

### Math Operations
- **Vector operations**: ~1-10μs for 3D transformations
- **Quaternion conversions**: ~5-20μs
- **Distance calculations**: ~0.1-1μs
- **Memory usage**: Minimal, primarily NumPy arrays

### Serial Communication
- **Connection overhead**: ~10-50ms initial connection
- **Read/write operations**: ~0.1-10ms depending on data size
- **Memory usage**: ~1-5KB per connection plus buffers

## Thread Safety

All utilities are designed to be thread-safe:
- **Configuration**: Uses locks for caching and merging
- **Logging**: Python logging is thread-safe by design
- **Math**: Pure functions with no shared state
- **Serial**: Connection-level locking prevents concurrent access

## Error Handling and Recovery

### Configuration Errors
- **Missing files**: Falls back to defaults with warnings
- **Invalid YAML**: Logs error and uses previous valid config
- **Environment vars**: Uses defaults for missing variables

### Logging Errors
- **File write failures**: Falls back to console-only logging
- **Rotation failures**: Continues with current file, logs warnings
- **Handler errors**: Removes failed handlers, continues with others

### Math Errors
- **Singular matrices**: Returns identity matrix with warning
- **Domain errors**: Clamps values to valid ranges
- **Numerical overflow**: Uses stable algorithms and checks

### Serial Errors
- **Connection loss**: Automatic reconnection with backoff
- **Timeout**: Returns partial data or empty result
- **Invalid data**: Validates and sanitizes input/output

## Testing and Validation

### Unit Tests
Located in `tests/test_utils.py`:
```bash
pytest tests/test_utils.py -v
```

### Integration Tests
Located in `tests/integration/test_utils_integration.py`:
- Configuration loading with multiple files
- Logging output verification
- Serial communication with loopback
- Math function accuracy validation

### Performance Benchmarks
```bash
python -m pytest tests/test_utils.py::test_config_performance
python -m pytest tests/test_utils.py::test_math_performance
```

## Extension and Customization

### Adding New Utilities
1. Create new file in `utils/` directory
2. Implement functions/classes with comprehensive docstrings
3. Add exports to `__init__.py`
4. Write unit tests in `tests/test_utils.py`
5. Update this README with documentation

### Configuration Extensions
- Add new configuration sections to YAML files
- Implement validation in `config_loader.py`
- Support new environment variable patterns
- Add type checking and conversion

### Math Library Extensions
- Add domain-specific functions (robotics, control theory)
- Implement optimized algorithms for common operations
- Add numerical stability checks
- Support different coordinate systems

### Serial Protocol Extensions
- Add protocol-specific parsers (Modbus, CAN, custom)
- Implement connection pooling for multiple devices
- Add protocol simulation for testing
- Support different encoding schemes

## Troubleshooting Guide

### Configuration Issues
**Symptom**: Configuration loading fails or wrong values
**Solutions**:
1. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"`
2. Check file permissions: `ls -la config/`
3. Verify environment variables: `echo $ROBOT_ENV`
4. Test loading: `python -c "from utils.config_loader import load_config; print(load_config())"`

### Logging Problems
**Symptom**: Logs not appearing or wrong format
**Solutions**:
1. Check log level: Ensure level is set appropriately
2. Verify file permissions: `touch logs/test.log`
3. Test logger creation: `python -c "from utils.logger import get_logger; get_logger('test').info('test')"`
4. Check configuration: Look for logging section in config

### Math Calculation Errors
**Symptom**: Incorrect kinematic calculations or transformations
**Solutions**:
1. Verify input units (radians vs degrees)
2. Check coordinate system conventions
3. Test with known values and compare results
4. Use debugging prints to trace calculations

### Serial Communication Failures
**Symptom**: Device communication not working
**Solutions**:
1. List available ports: `python -c "from utils.serial_utils import list_ports; print(list_ports())"`
2. Test basic connectivity: Use `minicom` or `screen`
3. Verify baud rate and settings match device
4. Check cable connections and power
5. Test with different USB ports

### Performance Issues
**Symptom**: System running slower than expected
**Solutions**:
1. Profile code execution: `python -m cProfile main.py`
2. Check logging overhead: Reduce log levels in production
3. Monitor memory usage: Look for memory leaks
4. Optimize math operations: Use vectorized NumPy operations

## Dependencies

### Required Packages
```bash
pip install pyyaml      # YAML configuration parsing
pip install pyserial    # Serial communication
pip install numpy       # Mathematical operations
```

### Optional Packages
```bash
pip install pyqt5       # GUI configuration editor (future)
pip install matplotlib  # Plotting utilities (debugging)
```

## Future Enhancements

### Planned Features
- **Configuration GUI**: Visual configuration editor
- **Log Analysis Tools**: Automated log parsing and analysis
- **Math Visualization**: 3D pose and trajectory visualization
- **Serial Protocol Library**: Pre-built parsers for common protocols
- **Performance Monitoring**: Built-in profiling and metrics collection

### API Improvements
- **Async Support**: Asynchronous configuration loading
- **Type Hints**: Full type annotation coverage
- **Validation**: JSON Schema validation for configurations
- **Caching**: Redis/external caching for distributed systems

This utils module provides the essential foundation that enables reliable, maintainable, and high-performance operation of the Trashformer robotic system across all subsystems.
