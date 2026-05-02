# Integration Tests

This directory contains integration tests that verify complete system workflows and component interactions.

## Integration Test Files

- **test_full_pickup.py** - Full trash detection, approach, and pickup sequence integration test

## Integration Testing Strategy

Integration tests verify:
1. **Multi-component workflows** - Multiple subsystems working together
2. **State transitions** - Proper state machine behavior across the system
3. **Data flow** - Information flowing correctly between components
4. **Error handling** - System behavior under fault conditions
5. **Real-world scenarios** - Realistic operational sequences

## Example: Full Pickup Workflow

The full pickup test validates:
1. Vision system detects trash
2. Behavior state machine initiates approach
3. Drive system navigates toward target
4. Arm system extends for pickup
5. Gripper engages trash
6. Return to home position

```python
def test_full_pickup_sequence():
    """Test complete trash detection and pickup workflow"""
    robot = RobotSystem()
    robot.initialize()
    
    # Place test trash in field of view
    place_test_trash(position=(0.5, 0.3))
    
    # Start autonomous mode
    robot.set_mode("autonomous")
    
    # Wait for pickup to complete
    robot.wait_for_state("idle", timeout=30)
    
    # Verify trash was picked up
    assert robot.gripper.has_object()
    assert robot.position == HOME_POSITION
```

## Fixture Setup

### Hardware Mocking
For testing without physical hardware:
```python
@pytest.fixture
def robot_simulation():
    """Provide a simulated robot for testing"""
    with mock_hardware():
        robot = RobotSystem()
        yield robot
        robot.shutdown()
```

### Test Scenarios
Provide different test scenarios:
- Ideal conditions (trash at expected location)
- Degraded conditions (poor lighting, obstacles)
- Error conditions (connection loss, sensor failure)
- Edge cases (trash at boundary, moving obstacles)

## Running Integration Tests

```bash
# Run all integration tests
python -m pytest tests/integration/

# Run specific integration test with verbose output
python -m pytest tests/integration/test_full_pickup.py -v

# Run with hardware (if available)
python -m pytest tests/integration/ --with-hardware

# Run with simulation
python -m pytest tests/integration/ --simulation
```

## Writing Integration Tests

### Key Principles

1. **Use realistic scenarios** - Test actual use cases
2. **Test happy path first** - Then error conditions
3. **Clean up state** - Leave system in known state
4. **Log extensively** - Integration tests report on many components
5. **Use timeouts** - Prevent hanging on unexpected failures

### Template

```python
import pytest
from robot.robot_system import RobotSystem

@pytest.mark.integration
class TestPickupWorkflow:
    
    def setup_method(self):
        """Initialize robot for each test"""
        self.robot = RobotSystem()
        self.robot.initialize()
    
    def teardown_method(self):
        """Clean up after each test"""
        self.robot.shutdown()
    
    @pytest.mark.timeout(60)  # 60 second timeout
    def test_detect_and_pick_trash(self):
        """Verify trash detection and pickup sequence"""
        # Setup
        self.robot.set_mode("autonomous")
        place_test_trash((0.5, 0.3, 0.0))
        
        # Execute
        self.robot.run_until(state="idle", timeout=30)
        
        # Verify
        assert self.robot.trash_collected > 0
        assert self.robot.position_matches(HOME, tolerance=0.1)
```

## Test Scenarios

### Normal Operation
- Detect and pick single trash item
- Navigate around obstacles
- Return to base station
- Repeated operations

### Degraded Conditions
- Low battery warning
- Sensor noise or interference
- Partial visibility (dirty lens)
- Network latency for remote operation

### Error Conditions
- Motor failure
- Sensor disconnection
- Control loss (E-stop pressed)
- Unexpected obstacles

### Edge Cases
- Trash at movement boundaries
- Multiple trash items in vicinity
- Trash partially visible
- Very close and far distances

## Continuous Integration

Integration tests should run:
- Nightly (full hardware testing)
- On pull requests (simulation testing)
- Before releases (complete validation)

Expected runtime:
- Simulation: 5-15 minutes
- Hardware: 30-60 minutes
- Full test suite: 60-120 minutes

## Debugging Integration Tests

```bash
# Run with verbose output and print statements
python -m pytest tests/integration/ -vv -s

# Run with interactive debugger
python -m pytest tests/integration/ --pdb

# Generate test report with HTML
python -m pytest tests/integration/ --html=report.html
```

## Test Data and Logging

Each integration test generates:
- **Test log** - System behavior during test
- **Sensor data** - Raw sensor readings
- **Performance metrics** - Timing information
- **Video/images** - If vision tests (if enabled)

Access logs in:
- `logs/integration_test_<timestamp>.log`

## Performance Baseline

Track integration test performance:
- Pickup completion time
- Detection latency
- Navigation accuracy
- Command response time

Establish baseline and alert on regressions.
