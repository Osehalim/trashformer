# Behavior Module

This module implements the robot's high-level behavioral intelligence and task orchestration. It contains the state machine that coordinates all subsystems (drive, arm, vision, sensors) to perform autonomous trash pickup operations. The behavior system is the "brain" of the robot, making decisions about what to do next based on sensor inputs and current goals.

## Module Architecture Overview

```
Vision System (detects trash)
    ↓
Behavior State Machine (decides what to do)
    ↓
Subsystems Coordination:
├── Drive Controller (navigation/movement)
├── Arm Controller (pickup motions)
├── Safety System (emergency overrides)
└── Sensor Fusion (state estimation)
```

## Files and Detailed Descriptions

### **state_machine.py** - Core behavioral state machine
Implements finite state machine for robot behavior coordination:

**Key states (typical implementation):**
- **IDLE**: Robot is stopped, waiting for commands
- **SEARCHING**: Autonomous search pattern for trash
- **APPROACHING**: Moving toward detected trash target
- **ALIGNING**: Fine positioning for pickup
- **PICKUP**: Executing arm motions to grasp trash
- **RETURNING**: Moving back to base station
- **ERROR**: Handling failures and recovery

**State machine implementation:**
```python
from enum import Enum

class RobotState(Enum):
    IDLE = "idle"
    SEARCHING = "searching"
    APPROACHING = "approaching"
    ALIGNING = "aligning"
    PICKUP = "pickup"
    RETURNING = "returning"
    ERROR = "error"

class BehaviorStateMachine:
    def __init__(self):
        self.current_state = RobotState.IDLE
        self.state_data = {}  # State-specific data
        
    def update(self, sensor_data, vision_data):
        """Main state machine update loop"""
        
        if self.current_state == RobotState.IDLE:
            # Check for start command or autonomous trigger
            if self.should_start_search():
                self.transition_to(RobotState.SEARCHING)
                
        elif self.current_state == RobotState.SEARCHING:
            # Look for trash via vision system
            if vision_data.has_targets():
                target = vision_data.get_closest_target()
                self.state_data['target'] = target
                self.transition_to(RobotState.APPROACHING)
                
        elif self.current_state == RobotState.APPROACHING:
            # Move toward target
            target = self.state_data['target']
            if self.is_close_enough(target):
                self.transition_to(RobotState.ALIGNING)
                
        elif self.current_state == RobotState.ALIGNING:
            # Fine positioning for pickup
            if self.is_aligned_for_pickup():
                self.transition_to(RobotState.PICKUP)
                
        elif self.current_state == RobotState.PICKUP:
            # Execute pickup sequence
            if self.pickup_complete():
                self.transition_to(RobotState.RETURNING)
                
        elif self.current_state == RobotState.RETURNING:
            # Return to base
            if self.at_base_station():
                self.transition_to(RobotState.IDLE)
                
        elif self.current_state == RobotState.ERROR:
            # Handle errors and attempt recovery
            if self.can_recover():
                self.transition_to(RobotState.IDLE)
```

**Location:** `behavior/state_machine.py` - `BehaviorStateMachine` class

**State transition logic:**
- **Triggers**: Sensor data, vision detections, timeouts, errors
- **Guards**: Safety checks, resource availability, system status
- **Actions**: Command subsystems, update internal state, log events

### **trash_pickup.py** - Trash pickup sequence logic
Handles the detailed sequence of motions for picking up trash:

**Pickup sequence (typical):**
1. **Approach**: Move robot close to trash (within arm reach)
2. **Position**: Fine-tune robot position for optimal grip
3. **Pre-grasp**: Open gripper, position arm above trash
4. **Descend**: Lower arm toward trash
5. **Grasp**: Close gripper on trash
6. **Lift**: Raise arm with trash
7. **Verify**: Check if pickup successful
8. **Stow**: Move arm to safe carrying position

```python
class TrashPickupBehavior:
    def __init__(self, arm_controller, drive_controller):
        self.arm = arm_controller
        self.drive = drive_controller
        self.pickup_state = "approach"
        
    def execute_pickup(self, target_position):
        """Execute complete pickup sequence"""
        
        if self.pickup_state == "approach":
            # Move robot close to trash
            distance = self.get_distance_to_target(target_position)
            if distance > 0.3:  # 30cm approach distance
                self.drive.move_toward(target_position)
            else:
                self.pickup_state = "position"
                
        elif self.pickup_state == "position":
            # Fine positioning
            if self.is_properly_positioned(target_position):
                self.pickup_state = "pre_grasp"
                
        elif self.pickup_state == "pre_grasp":
            # Open gripper, position above trash
            self.arm.open_gripper()
            self.arm.move_to_position(target_position + [0, 0, 0.1])  # 10cm above
            self.pickup_state = "descend"
            
        elif self.pickup_state == "descend":
            # Lower toward trash
            self.arm.move_to_position(target_position)
            if self.arm.at_target():
                self.pickup_state = "grasp"
                
        elif self.pickup_state == "grasp":
            # Close gripper
            self.arm.close_gripper()
            time.sleep(0.5)  # Wait for grasp
            self.pickup_state = "lift"
            
        elif self.pickup_state == "lift":
            # Raise arm
            self.arm.move_to_position(target_position + [0, 0, 0.3])  # Lift 30cm
            if self.arm.at_target():
                self.pickup_state = "verify"
                
        elif self.pickup_state == "verify":
            # Check if pickup successful
            if self.verify_pickup():
                self.pickup_state = "stow"
            else:
                self.pickup_state = "retry"
                
        elif self.pickup_state == "stow":
            # Move to safe carrying position
            self.arm.move_to_stow_position()
            self.pickup_state = "complete"
```

**Location:** `behavior/trash_pickup.py` - `TrashPickupBehavior` class

**Pickup challenges and solutions:**
- **Trash movement**: Trash may shift during approach
- **Unstable grasp**: Different trash shapes/sizes
- **Obstacle avoidance**: Don't hit other objects
- **Recovery**: What to do if pickup fails

### **navigation.py** - Navigation and path planning
Handles autonomous movement and obstacle avoidance:

**Navigation modes:**
- **Search pattern**: Systematic coverage of area
- **Direct approach**: Move straight toward target
- **Obstacle avoidance**: Navigate around obstacles
- **Return to base**: Path back to starting location

**Search patterns:**
- **Spiral**: Expanding spiral from center
- **Lawn mower**: Back-and-forth rows
- **Random walk**: Brownian motion exploration
- **Boundary following**: Wall-following behavior

```python
class NavigationBehavior:
    def __init__(self, drive_controller, sensor_fusion):
        self.drive = drive_controller
        self.sensors = sensor_fusion
        self.current_goal = None
        
    def search_pattern(self):
        """Execute search pattern for trash"""
        # Implement spiral, lawn mower, or other pattern
        # Check for obstacles and adjust path
        # Return True when trash found or area covered
        
    def approach_target(self, target_position):
        """Move toward target with obstacle avoidance"""
        while not self.at_target(target_position):
            # Check for obstacles
            obstacles = self.sensors.get_obstacles()
            
            if obstacles:
                # Path around obstacles
                safe_path = self.plan_path_around_obstacles(target_position, obstacles)
                self.drive.follow_path(safe_path)
            else:
                # Direct path
                self.drive.move_toward(target_position)
                
    def return_to_base(self):
        """Navigate back to base station"""
        base_position = self.get_base_position()
        self.approach_target(base_position)
```

**Location:** `behavior/navigation.py` - `NavigationBehavior` class

**Path planning algorithms:**
- **A***: Optimal path finding with obstacle avoidance
- **RRT**: Rapidly-exploring random trees for complex environments
- **Potential fields**: Attractive/repulsive forces
- **Follow wall**: Boundary following for maze navigation

### **idle.py** - Idle and standby behaviors
Handles robot behavior when not actively working:

**Idle functions:**
- **Power management**: Reduce power consumption
- **System monitoring**: Check all subsystems health
- **Self-test**: Periodic system verification
- **Standby**: Ready for immediate activation

```python
class IdleBehavior:
    def __init__(self, robot_system):
        self.robot = robot_system
        self.idle_start_time = None
        
    def enter_idle(self):
        """Enter idle state"""
        self.idle_start_time = time.time()
        self.robot.drive.stop()  # Stop movement
        self.robot.arm.stow()    # Safe arm position
        
    def update_idle(self):
        """Periodic idle tasks"""
        # Check system health
        if not self.robot.safety.is_system_healthy():
            self.robot.behavior.set_state("ERROR")
            return
            
        # Periodic self-test
        if time.time() - self.idle_start_time > 300:  # Every 5 minutes
            self.run_self_test()
            
        # Check for activation triggers
        if self.should_activate():
            self.robot.behavior.set_state("SEARCHING")
```

**Location:** `behavior/idle.py` - `IdleBehavior` class

### **parameters.yaml** - Behavior configuration
Configuration parameters for behavior tuning:

```yaml
behavior:
  # Search parameters
  search:
    pattern: "spiral"  # spiral, lawn_mower, random
    area_width: 5.0    # meters
    area_height: 5.0
    speed: 0.3         # m/s during search
    
  # Approach parameters
  approach:
    approach_distance: 0.3  # meters from trash
    alignment_tolerance: 0.05  # meters positioning accuracy
    approach_speed: 0.2     # m/s
    
  # Pickup parameters
  pickup:
    pre_grasp_height: 0.1   # meters above trash
    grasp_force: 50         # gripper force (0-100)
    lift_height: 0.3        # meters to lift after grasp
    timeout: 10.0           # seconds max pickup time
    
  # Navigation
  navigation:
    obstacle_margin: 0.2    # meters clearance
    max_turn_rate: 1.0      # rad/s
    path_resolution: 0.1    # meters
    
  # State machine
  state_machine:
    transition_timeout: 30.0  # seconds max per state
    error_recovery_attempts: 3
```

**Location:** `behavior/parameters.yaml`

## How Everything Works Together

### Main Control Loop

```python
# Initialize all systems
robot = RobotSystem()
behavior = BehaviorStateMachine(robot)

# Main behavior loop (runs at ~10-30 Hz)
while robot.is_running():
    # Get current sensor/vision data
    sensor_data = robot.sensors.get_fused_data()
    vision_data = robot.vision.get_detections()
    
    # Update behavior state machine
    behavior.update(sensor_data, vision_data)
    
    # Execute current behavior
    current_state = behavior.get_current_state()
    
    if current_state == RobotState.SEARCHING:
        robot.navigation.execute_search()
        
    elif current_state == RobotState.APPROACHING:
        target = behavior.get_target()
        robot.navigation.approach_target(target)
        
    elif current_state == RobotState.PICKUP:
        robot.pickup.execute_pickup_sequence()
        
    # Safety check (always runs)
    if robot.safety.emergency_stop_triggered():
        behavior.force_state(RobotState.IDLE)
        robot.drive.emergency_stop()
```

## Important Configuration Files

**Behavior parameters:** `behavior/parameters.yaml`
- Search patterns and speeds
- Approach distances and tolerances
- Pickup timing and forces
- Navigation safety margins

**Hardware config:** `config/hardware_config.yaml`
```yaml
behavior:
  update_rate: 20  # Hz
  enable_autonomous: true
  safety_override: false
```

**Default config:** `config/default.yaml`
- Base behavior settings
- Environment-specific overrides

**Logs:** `logs/trashformer_*.log` - Search for "behavior" or state names

## Common Issues and Debugging

### Issue: Robot gets stuck in SEARCHING state

**Root causes:**

1. **Vision system not detecting trash**
   - Check vision system is running: `python tools/camera_preview.py`
   - Verify confidence threshold not too high in `vision/vision_config.yaml`
   - Test detection manually

2. **Search area too small**
   ```yaml
   # In behavior/parameters.yaml
   search:
     area_width: 10.0  # Increase search area
     area_height: 10.0
   ```

3. **No trash in area**
   - Verify test environment has detectable trash
   - Check lighting conditions
   - Use `tools/camera_preview.py` to verify camera view

4. **State machine not transitioning**
   ```python
   # Debug: Check state machine logic
   print(f"Current state: {behavior.current_state}")
   print(f"Vision targets: {len(vision_data.targets)}")
   print(f"Should transition: {behavior.should_transition()}")
   ```

### Issue: Robot approaches trash but misses pickup

**Debug approach positioning:**

1. **Check target coordinates**
   ```python
   # Print target position before approach
   target = behavior.get_target()
   print(f"Target position: {target['position']}")
   print(f"Target confidence: {target['confidence']}")
   ```

2. **Verify coordinate transforms**
   - Camera coordinates → Robot coordinates
   - Check camera calibration: `data/calibration/camera_params.json`
   - Test with known object at known position

3. **Approach distance too far**
   ```yaml
   # In behavior/parameters.yaml
   approach:
     approach_distance: 0.2  # Reduce to 20cm
   ```

4. **Arm reach limitations**
   - Check arm workspace limits in `arm/poses.yaml`
   - Verify target within arm reach envelope

5. **Timing issues**
   ```python
   # Add debug timing
   start_time = time.time()
   # ... approach logic ...
   elapsed = time.time() - start_time
   print(f"Approach took {elapsed:.2f}s")
   ```

### Issue: Pickup sequence fails partway through

**Common failure points:**

1. **Gripper not opening/closing**
   - Check servo power and connections
   - Test gripper manually: `python tools/test_arm.py`
   - Verify servo limits in `data/calibration/servo_limits.json`

2. **Arm not reaching position**
   ```python
   # Debug arm positioning
   target_pos = [0.5, 0.0, 0.3]  # Example
   success = robot.arm.move_to_position(target_pos)
   if not success:
       print("Arm move failed - check kinematics")
       print(f"Current position: {robot.arm.get_position()}")
   ```

3. **Trash moving during approach**
   - Increase approach speed for faster pickup
   - Or add position tracking during pickup

4. **Collision detection**
   - Check for limit switches triggering
   - Verify arm not hitting obstacles

5. **Timeout issues**
   ```yaml
   # Increase pickup timeout
   pickup:
     timeout: 20.0  # 20 seconds
   ```

### Issue: Robot doesn't return to base properly

**Navigation debugging:**

1. **Base position not set**
   ```python
   # Verify base position stored
   base_pos = robot.navigation.get_base_position()
   print(f"Base position: {base_pos}")
   ```

2. **Path planning failing**
   - Check for obstacles blocking return path
   - Verify odometry accuracy (wheel encoders)
   - Test navigation manually

3. **Coordinate system issues**
   - Base position in wrong coordinate frame
   - Check IMU calibration for heading

4. **Drive system problems**
   - Test drive manually: `python tools/test_drive.py`
   - Check motor controllers and encoders

### Issue: State machine transitions too slowly

**Performance issues:**

1. **Update rate too low**
   ```yaml
   # In hardware_config.yaml
   behavior:
     update_rate: 30  # Increase to 30 Hz
   ```

2. **Blocking operations**
   - Vision detection taking too long
   - Arm movements blocking state machine
   - Use async operations where possible

3. **Sensor delays**
   - IMU filtering lag
   - Camera frame rate too low
   - Optimize sensor fusion settings

### Issue: Robot oscillates or has unstable behavior

**Control stability problems:**

1. **PID tuning issues**
   - Check drive PID gains in `drive/pid.yaml`
   - Too high gain → oscillation
   - Too low gain → slow response

2. **Sensor noise**
   - IMU drift causing position errors
   - Recalibrate IMU: `python tools/calibrate_imu.py`

3. **State machine hysteresis**
   - Add hysteresis to state transitions
   - Prevent rapid state switching

4. **Timing issues**
   - Inconsistent loop timing
   - Add fixed update rate with proper timing

## Where to Find Everything

**State machine code:** `behavior/state_machine.py` - `BehaviorStateMachine` class
**Pickup logic:** `behavior/trash_pickup.py` - `TrashPickupBehavior` class
**Navigation:** `behavior/navigation.py` - `NavigationBehavior` class
**Idle behavior:** `behavior/idle.py` - `IdleBehavior` class

**Configuration files:**
- `behavior/parameters.yaml` - Behavior tuning parameters
- `config/hardware_config.yaml` - System configuration
- `config/default.yaml` - Base settings

**Related modules:**
- `arm/` - Arm control for pickup motions
- `drive/` - Drive control for movement
- `vision/` - Trash detection
- `sensors/` - State estimation
- `safety/` - Emergency overrides

**Log files:**
- `logs/trashformer_*.log` - Search for "behavior", "state", or specific state names
- Real-time logging in debug mode

**Test tools:**
- `python tools/test_arm.py` - Test arm pickup motions
- `python tools/test_drive.py` - Test navigation
- `python tools/camera_preview.py` - Verify vision input

## Performance Optimization

**Behavior update timing (typical 20 Hz):**
```
Sensor reading:     5ms
Vision processing: 15ms (bottleneck!)
State decision:     2ms
Command execution:  3ms
Total:             25ms (40 Hz max)
```

**Optimization strategies:**

1. **Parallel processing**
   - Vision detection in separate thread
   - Sensor fusion async
   - State machine runs at fixed rate

2. **State caching**
   - Cache expensive computations
   - Only recalculate when inputs change
   - Use prediction for intermediate frames

3. **Hierarchical states**
   - High-level: SEARCH → APPROACH → PICKUP
   - Low-level: Fine motion control within states
   - Reduces decision frequency

4. **Event-driven transitions**
   - Don't poll constantly
   - Use callbacks for state changes
   - Interrupt-driven for fast reactions

## Advanced Debugging

### Visualize state machine
```python
# Log state transitions
def log_state_transition(from_state, to_state, reason):
    timestamp = time.time()
    print(f"{timestamp}: {from_state} → {to_state} ({reason})")
    
    # Also write to file
    with open('state_log.txt', 'a') as f:
        f.write(f"{timestamp},{from_state},{to_state},{reason}\n")

# In state machine
self.log_transition(self.current_state, new_state, trigger_reason)
```

### Profile behavior performance
```python
import time

class BehaviorProfiler:
    def __init__(self):
        self.update_times = []
        
    def start_update(self):
        self.update_start = time.time()
        
    def end_update(self):
        elapsed = time.time() - self.update_start
        self.update_times.append(elapsed)
        
        # Print stats every 100 updates
        if len(self.update_times) % 100 == 0:
            avg_time = sum(self.update_times[-100:]) / 100
            print(f"Avg update time: {avg_time*1000:.1f}ms ({1/avg_time:.1f} Hz)")

# Usage
profiler = BehaviorProfiler()
while running:
    profiler.start_update()
    # ... behavior update logic ...
    profiler.end_update()
```

### Record behavior sessions
```python
# Save complete behavior traces for analysis
behavior_trace = {
    'timestamp': [],
    'state': [],
    'sensor_data': [],
    'vision_data': [],
    'commands': []
}

def record_frame(state, sensors, vision, commands):
    behavior_trace['timestamp'].append(time.time())
    behavior_trace['state'].append(state)
    behavior_trace['sensor_data'].append(sensors)
    behavior_trace['vision_data'].append(vision)
    behavior_trace['commands'].append(commands)

# Save to file periodically
import json
with open(f'behavior_trace_{int(time.time())}.json', 'w') as f:
    json.dump(behavior_trace, f)
```

### Simulate behavior offline
```python
# Test behavior logic without hardware
class MockRobot:
    def __init__(self):
        self.position = [0, 0, 0]
        self.arm_position = [0, 0, 0]
        
    def move_to(self, pos):
        self.position = pos
        return True
        
    def arm_move_to(self, pos):
        self.arm_position = pos
        return True

# Test pickup sequence
mock_robot = MockRobot()
pickup = TrashPickupBehavior(mock_robot, mock_robot)
pickup.execute_pickup([0.5, 0, 0.1])  # Test pickup at position
```
