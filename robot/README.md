# Robot Module

This module contains the main robot system orchestrator that manages all subsystems, their initialization, coordination, and shutdown. Think of it as the "brain" that makes all the individual components work together as a cohesive system.

## Module Architecture

```
RobotSystem (main orchestrator)
├── Drive subsystem
├── Arm subsystem  
├── Sensors subsystem
├── Vision subsystem
├── Behavior state machine
├── Safety systems
├── Teleoperation handler
├── Logger (centralized logging)
└── Timing utilities (performance monitoring)
```

## Files and Detailed Descriptions

### **robot_system.py** - Main coordinator
The core class that holds everything together:
- `RobotSystem` class - Initialization, startup, operation, shutdown
- Subsystem lifecycle management (initialize → run → shutdown)
- Inter-module communication and data sharing
- Error handling and recovery
- Operational mode switching (autonomous, teleoperation, simulation)

**Key responsibilities:**
- Initialize hardware in correct order (safety systems first, then drive/arm, then vision)
- Maintain shared state (current mode, active errors, system health)
- Coordinate timing across subsystems
- Handle exceptions and prevent system crashes
- Provide unified interface to external code

**Example usage:**
```python
from robot.robot_system import RobotSystem

robot = RobotSystem()            # Create instance
robot.initialize()               # Setup hardware
robot.set_mode("autonomous")    # Choose operation mode
robot.run()                      # Main control loop
robot.shutdown()                 # Cleanup and stop
```

**Location:** `robot/robot_system.py` - `RobotSystem` class definition

**Key variables:**
- `self.mode` - Current operation mode (string)
- `self.running` - System active flag
- `self.subsystems` - Dictionary of all subsystem managers
- `self.state` - Current system state (idle, operating, error, etc.)
- `self.health_status` - Status of each subsystem

### **logger.py** - Centralized logging
Unified logging system for the entire robot:
- Sets up logging to console and file
- Module-specific loggers with hierarchy
- Configurable log levels
- Timestamp and context information
- Log rotation for long-running systems

**How logging works in the system:**
```python
from robot.logger import get_logger

# In any module
logger = get_logger('arm.controller')  # Hierarchical name
logger.info("Arm initialized")
logger.warning("Joint 3 at torque limit")
logger.error("Servo communication failed!")
```

**Log level hierarchy (from least to most verbose):**
- `WARNING` - Only important issues (errors, critical warnings)
- `INFO` - General operation events (mode changes, milestones)
- `DEBUG` - Detailed operational info (sensor readings, commands)
- `DEBUG_VERBOSE` - Very detailed (every calculation, every sensor tick)

**Log output locations:**
- Console: All WARNING and above (real-time monitoring)
- File: All messages (full record)
- Files stored in: `logs/` directory
- Filename format: `logs/trashformer_YYYYMMDD_HHMMSS.log`

**Finding specific messages:**
```bash
# Search log for arm-related messages
grep "arm\|ARM" logs/trashformer_*.log

# See only errors
grep "ERROR\|WARNING" logs/trashformer_*.log

# Tail live log file (follow in real-time)
tail -f logs/trashformer_*.log
```

**Location:** `robot/logger.py` - `get_logger()` function

**Configuration:**
- Log level in `config/default.yaml` under `logging.level`
- Log file path in same config under `logging.file_path`
- Console output colorization (if supported)

### **timing.py** - Performance monitoring
Utilities for measuring execution time and system performance:
- `Timer` class for stopwatch-like timing
- Performance profiling of operations
- Frame rate monitoring
- Latency detection

**How to use timing:**
```python
from robot.timing import Timer

timer = Timer()

# Measure specific operation
with timer.measure("image_processing"):
    frame = camera.read()
    detections = detector.detect(frame)

# Check performance
print(timer.report())  # Shows average, min, max times
```

**Performance report example:**
```
Performance Report:
  Operation              Count   Avg(ms)  Min(ms)  Max(ms)
  image_processing         50    125.3     98.2    202.1
  motor_command          1000     2.1      1.8      5.2
  encoder_read           1000     1.5      1.2      4.3
```

**Finding bottlenecks:**
Look for operations with high max times or high variability → indicates inconsistent timing or CPU contention

**Location:** `robot/timing.py` - `Timer` and `FrameRateCounter` classes

## System Lifecycle

### Initialization (startup)

```python
robot = RobotSystem()
robot.initialize()
```

**What happens during initialization (in order):**

1. **Safety systems first**
   - Initialize E-stop (must respond to panic button)
   - Load safety interlocks
   - Start watchdog timer
   - *Why first:* Safety override everything; must work immediately

2. **Logging**
   - Create log file
   - Set up logger
   - *Why early:* Need logging for all subsequent initialization messages

3. **Configuration loading**
   - Load yaml configs from `config/` directory
   - Merge hardware-specific overrides
   - Apply environment variable substitutions
   - *Where:* `config/hardware_config.yaml`, `config/default.yaml`, etc.

4. **Hardware drivers**
   - Initialize motor controllers (Roboclaw, Sabertooth)
   - Initialize servo controller (PCA9685)
   - Initialize sensors (IMU, distance sensors, encoders)
   - Test communication (will raise exception if hardware not responding)
   - *Where:* `config/hardware_config.yaml` defines pin/port assignments

5. **Subsystem initialization**
   - Create Drive module
   - Create Arm module  
   - Create Vision module (involves loading ML model, can be slow)
   - Create Behavior state machine
   - *Order matters:* Drive before Behavior (Behavior uses drive commands)

6. **Self-tests**
   - Verify each subsystem responding correctly
   - Check sensor validity
   - May run quick calibration if needed

If any initialization step fails:
- Exception is raised with descriptive error message
- Partially initialized subsystems are cleaned up
- Log file contains details of failure
- Check logs: `logs/trashformer_*.log` - search for "ERROR"

### Main Operation Loop

```python
robot.run()  # Blocks while running
```

**Typical control loop:**
```
while robot.running:
    1. Check safety systems (E-stop, watchdog)
    2. Read all sensors (IMU, encoders, TOF sensors)
    3. Run behavior/autonomous logic (state machine)
    4. Update arm/drive based on behavior output
    5. Send motor commands to hardware
    6. Update telemetry (logging, display)
    7. Sleep remainder of cycle (e.g., 50ms for 20Hz rate)
```

**Control rate:** Typically 20-50 Hz (cycle every 50-20ms)

**What determines control rate:**
- Configured in `config/default.yaml` under `control_rate_hz`
- Limited by slowest operation in loop
- Must be fast enough reactions required by task
- Faster = more responsive but uses more CPU

### Shutdown

```python
robot.shutdown()
```

**Cleanup sequence:**
1. Set running flag to False (stops main loop)
2. Stop all motors immediately (safety)
3. Close servo connections
4. Close sensor connections
5. Close serial ports
6. Close log file
7. Release resources

**Why order matters:**
- Motors stopped first (physical safety)
- Then hardware closed (prevents resource leaks)

## Operational Modes

The robot can operate in different modes:

### Autonomous Mode
```python
robot.set_mode("autonomous")
```
- Vision system detects trash
- Behavior state machine plans actions
- Drive/arm execute pickups
- No external input needed
- Location: `behavior/state_machine.py`

### Teleoperation Mode
```python
robot.set_mode("teleop")
```
- External controller (gamepad, keyboard) provides commands
- Robot relays commands to drive/arm
- Vision provides feedback to operator
- Location: `teleop/` module

### Simulation Mode
```python
robot.set_mode("simulation")
```
- Uses mock hardware instead of real
- Useful for development without robot present
- Predictable behavior for testing
- Location: Controlled in config with `simulation_mode: true`

### Manual/Debug Mode
```python
robot.set_mode("manual")
```
- Direct low-level control
- For testing individual components
- Bypasses normal safety checks (be careful!)

Mode switching example:
```python
if manual_override_button_pressed():
    robot.set_mode("manual")
    robot.drive.set_velocity(user_input_linear, user_input_angular)
```

## Subsystem Coordination

### Data Flow Between Subsystems

```
Sensors
  ├─> Vision (detect trash)
  ├─> IMU/Encoders (position)
  └─> Distance sensors (obstacles)
  
        ↓
        
Behavior state machine
  ├─> Decides next action
  └─> Generates drive/arm commands

        ↓

Drive + Arm
  ├─> Execute movement
  └─> Provide feedback

        ↓

Logging + Telemetry
  └─> Record for debugging
```

### Example: Trash Pickup Sequence

```python
# This is what drives the whole system

# Step 1: Sensor reads trash
trash_detected = vision.detect_trash(frame)

# Step 2: Behavior state machine processes
behavior.process_detection(trash_detected)
behavior.update()  # State machine logic

# Step 3: Behavior generates commands
drive_cmd = behavior.get_drive_command()
arm_cmd = behavior.get_arm_command()

# Step 4: Subsystems execute
drive.set_velocity(drive_cmd.linear, drive_cmd.angular)
arm.move_to_pose(arm_cmd.pose)

# Step 5: Logging records everything
logger.info(f"Detected trash at {trash_detected.position}")
logger.debug(f"State: {behavior.current_state}")
logger.debug(f"Drive: {drive_cmd}, Arm: {arm_cmd}")

# ... repeat at control rate until pickup done ...
```

## Common Issues and Debugging

### Issue: Robot won't start (initialize fails)

**Where to look for error:**
1. Log file: `logs/trashformer_*.log` 
   - Look for first "ERROR" message
   - This tells you which subsystem failed

2. Console output during startup
   - Will show exception traceback
   - Look at last few lines for specific error

**Common initialization failures:**

1. **Motor controller not found**
   - Error: "Failed to open serial port /dev/ttyUSB0"
   - Fix: 
     - Verify USB cable connected
     - List ports: `ls /dev/ttyUSB*` or Device Manager on Windows
     - Update port in `config/hardware_config.yaml`

2. **Servo controller (PCA9685) not responding**
   - Error: "I2C address 0x40 not found"
   - Fix:
     - Check I2C wiring (SDA, SCL, GND, VCC)
     - Verify I2C bus in config: `i2cdetect -y 1` on Linux
     - Confirm PCA9685 powered correctly (3.3V or 5V)

3. **IMU not responding**
   - Error: "Failed to initialize IMU"
   - Fix:
     - Check I2C address matches hardware
     - Verify wiring
     - Try another I2C address if DIP-switch configurable

4. **ML model file not found**
   - Error: "Cannot load model: models/trash_detector.pt not found"
   - Fix:
     - Download model to `models/` directory
     - Update path in `vision/vision_config.yaml`

### Issue: System runs but behaves unexpectedly

**Systematic approach:**

1. **Check operational mode**
   ```python
   print(f"Current mode: {robot.mode}")
   print(f"Current state: {robot.state}")
   ```
   - Is it the mode you expect?
   - Is it in expected state?

2. **Enable debug logging**
   - Edit `config/default.yaml`
   - Change `logging.level: DEBUG` (or `DEBUG_VERBOSE`)
   - Restart robot
   - Look for additional detail in `logs/trashformer_*.log`

3. **Check subsystem health**
   ```python
   print(robot.health_status)
   ```
   - Shows status of each subsystem
   - Any subsystem reporting error?

4. **Isolate the problem**
   - Temporarily disable subsystems to narrow down
   - Example: In `robot_system.py`, comment out vision init:
     ```python
     # self.vision = VisionSystem()  # Temporarily disabled
     ```
   - Restart and see if system works better

### Issue: Subsystem behaves incorrectly

**Example: Arm moves wrong direction**

1. Check arm subsystem directly:
   ```bash
   python tools/test_arm_full.py
   ```
   - Does it behave correctly in isolation?
   - If yes: Problem is in behavior state machine / arm_teleop
   - If no: Problem is in arm module itself

2. Check robot system's arm reference:
   ```python
   print(robot.arm)
   robot.arm.move_to_pose("home")  # Direct test
   ```

3. If direct command works but autonomous doesn't:
   - Behavior state machine is sending wrong commands
   - Check `behavior/state_machine.py`
   - Add debug logging in state transition code

### Issue: System slow or jerky

**Performance debugging:**

1. Check control rate:
   ```python
   print(robot.timings)  # Shows loop timing statistics
   ```
   - Is actual rate matching configured rate?
   - If slower: Some operation is taking too long

2. Find the slow operation:
   ```python
   # In robot_system.py, add timer around each step
   with timer.measure("vision_update"):
       self.vision.update()
   
   with timer.measure("behavior_step"):
       self.behavior.step()
   
   with timer.measure("arm_command"):
       self.arm.execute_command()
   ```
   - Check `timer.report()` to see which takes longest

3. Optimize slowest part:
   - Vision slow: Skip frames, reduce resolution
   - Behavior slow: Optimize state machine logic
   - Drivers slow: Check serial communication speed, I2C frequency

## Where to Find Important Configuration

**Main system settings:** `config/default.yaml`
```yaml
system:
  mode: "autonomous"  # or "teleop", "simulation"
  control_rate_hz: 20  # Main loop frequency
  log_level: "INFO"  # or "DEBUG" for verbose logging

simulation:
  enabled: false  # Set to true for sim mode

subsystems:
  enable_vision: true
  enable_arm: true
  enable_drive: true
  enable_safety: true
```

**Hardware specifics:** `config/hardware_config.yaml`
```yaml
hardware:
  platform: "raspberry_pi"  # or specific platform
  i2c_bus: 1
  
  # Each subsystem section...
```

**Using different configs:**
```bash
# Use development settings
CONFIG=development.yaml python main.py

# Or
robot = RobotSystem(config_file="development.yaml")
```

**Log file location:** `logs/trashformer_YYYYMMDD_HHMMSS.log`
- Create log subdirectory if not exists
- New log file per startup
- Old logs kept for reference

## Advanced Topics

### Multi-threaded Subsystems

Some subsystems may run in separate threads (vision, sensors) for responsiveness:

```python
class RobotSystem:
    def initialize(self):
        # Create sensor thread
        self.sensor_thread = Thread(target=self._sensor_loop)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()
        
        # Create vision thread
        self.vision_thread = Thread(target=self._vision_loop)
        self.vision_thread.daemon = True
        self.vision_thread.start()
        
        # Main thread runs behavior/drive
```

Thread safety considerations:
- Use locks for shared data
- Queues for thread communication
- Timing offsets to avoid resource contention

### Extending for New Subsystems

Adding a new subsystem (e.g., manipulator widget):

```python
class RobotSystem:
    def initialize(self):
        # ... existing code ...
        self.widget = WidgetSubsystem()
        self.widget.initialize()
        self.subsystems['widget'] = self.widget
    
    def _update_loop(self):
        # ... existing updates ...
        widget_cmd = self.behavior.get_widget_command()
        self.widget.execute(widget_cmd)
```

### Performance Profiling

For detailed performance analysis:
```python
import cProfile

def main():
    robot = RobotSystem()
    robot.initialize()
    robot.run()

cProfile.run('main()', sort='cumtime')  # Most time-consuming functions first
```

### Graceful Error Recovery

If a subsystem fails during operation:
```python
try:
    self.arm.move_to_pose("pickup")
except Exception as e:
    logger.error(f"Arm movement failed: {e}")
    self.behavior.handle_arm_failure()
    # Continue with degraded functionality
```
