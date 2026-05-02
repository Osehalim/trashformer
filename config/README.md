# Config Module

This directory contains all configuration files for the robot system, including hardware settings, development environments, and default parameters.

## Files

- **default.yaml** - Default configuration used across all modules
- **development.yaml** - Development environment overrides
- **hardware_config.yaml** - Hardware-specific settings (motors, servos, sensors)

## Configuration Hierarchy

Configurations are loaded in the following priority order (highest to lowest):
1. Environment-specific config (e.g., development.yaml)
2. Hardware config (hardware_config.yaml)
3. Default config (default.yaml)

## Typical Settings

### default.yaml
- System parameters
- Communication timeouts
- Safety thresholds
- Log levels

### hardware_config.yaml
- Motor specifications
- Servo pin assignments
- Sensor calibration values
- Communication ports

### development.yaml
- Debug flags
- Verbose logging
- Simulation mode settings
- Testing parameters

## Usage

```python
from utils.config_loader import load_config

config = load_config()
motor_speed = config['drive']['max_speed']
```

## Adding New Configuration Keys

When adding new configuration keys:
1. Add defaults to default.yaml
2. Add hardware-specific overrides to hardware_config.yaml
3. Add development overrides to development.yaml
4. Update documentation in this README
