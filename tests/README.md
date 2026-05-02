# Tests Directory

This directory contains comprehensive test suites for the Trashformer robotic system, including unit tests, integration tests, system tests, and test utilities. Testing ensures code quality, prevents regressions, and validates system functionality across all modules.

## Test Structure Overview

```
tests/
├── unit/                    # Unit tests (individual functions/classes)
│   ├── test_arm.py         # Arm controller and kinematics
│   ├── test_drive.py       # Drive system and motor control
│   ├── test_safety.py      # Safety systems and interlocks
│   ├── test_sensors.py     # Sensor interfaces and filtering
│   └── test_vision.py      # Vision and image processing
├── integration/            # Integration tests (module interactions)
│   ├── test_full_pickup.py # Complete pickup workflow
│   └── README.md          # Integration test documentation
├── system/                # System-level tests (end-to-end)
├── fixtures/              # Test data and mock objects
├── conftest.py            # pytest configuration and fixtures
└── README.md             # This file
```

## Test Categories and Purposes

### **Unit Tests** - Individual Component Testing
Test individual functions, classes, and modules in isolation:
- **Purpose**: Verify each component works correctly alone
- **Scope**: Single function/method/class
- **Dependencies**: Mocked or stubbed
- **Speed**: Fast (< 1 second per test)
- **Examples**: Test kinematics calculations, PID control, sensor filtering

### **Integration Tests** - Component Interaction Testing
Test how components work together:
- **Purpose**: Verify module interfaces and data flow
- **Scope**: Multiple related modules
- **Dependencies**: Real components (may use test fixtures)
- **Speed**: Medium (1-30 seconds per test)
- **Examples**: Arm + vision coordination, drive + safety interlocks

### **System Tests** - End-to-End Testing
Test complete system workflows:
- **Purpose**: Validate full user scenarios
- **Scope**: Entire robot system
- **Dependencies**: Real hardware or comprehensive simulation
- **Speed**: Slow (30+ seconds per test)
- **Examples**: Complete trash pickup sequence, autonomous navigation

## Running Tests

### **Prerequisites**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-xdist

# For hardware tests
pip install pytest-rerunfailures

# For test reporting
pip install pytest-html
```

### **Basic Test Execution**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_arm.py

# Run specific test function
pytest tests/test_arm.py::test_forward_kinematics

# Run tests matching pattern
pytest -k "kinematics"

# Run tests in specific directory
pytest tests/integration/
```

### **Advanced Test Options**
```bash
# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run with coverage
pytest --cov=. --cov-report=html

# Run in parallel (multiple CPUs)
pytest -n auto

# Rerun failed tests
pytest --rerun-failures=3

# Generate HTML report
pytest --html=report.html
```

### **Test Configuration**
**pytest.ini** (or pyproject.toml):
```ini
[tool:pytest.ini_options]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=. --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    system: System tests
    hardware: Requires physical hardware
    slow: Slow running tests
```

## Writing Tests

### **Test File Structure**
```python
import pytest
from unittest.mock import Mock, patch
from your_module import YourClass

class TestYourClass:
    """Test suite for YourClass"""
    
    @pytest.fixture
    def sample_config(self):
        """Fixture providing test configuration"""
        return {
            'param1': 'value1',
            'param2': 42
        }
    
    @pytest.fixture
    def mock_hardware(self):
        """Fixture providing mocked hardware"""
        mock = Mock()
        mock.get_position.return_value = 0.5
        return mock
    
    def test_initialization(self, sample_config):
        """Test object creation"""
        obj = YourClass(config=sample_config)
        assert obj.config == sample_config
    
    def test_method_with_mock(self, mock_hardware):
        """Test method using mocked dependency"""
        with patch('your_module.HardwareInterface', return_value=mock_hardware):
            obj = YourClass()
            result = obj.some_method()
            assert result == expected_value
    
    @pytest.mark.parametrize("input,expected", [
        (0, 0),
        (1, 1),
        (2, 4),
    ])
    def test_parameterized(self, input, expected):
        """Test with multiple input/output pairs"""
        assert some_function(input) == expected
```

### **Test Naming Conventions**
- **Files**: `test_*.py` or `*_test.py`
- **Classes**: `Test*` (e.g., `TestArmController`)
- **Functions**: `test_*` (e.g., `test_forward_kinematics`)
- **Fixtures**: `*_fixture` or just descriptive names

### **Test Markers**
```python
@pytest.mark.unit
def test_some_unit_test():
    pass

@pytest.mark.integration
def test_module_interaction():
    pass

@pytest.mark.hardware
def test_real_hardware():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

## Detailed Test Files

### **test_arm.py** - Arm System Testing
Tests robotic arm control, kinematics, and motion planning.

**Key test areas:**
- **Forward kinematics**: Joint angles → end-effector position
- **Inverse kinematics**: Target position → joint angles
- **Trajectory planning**: Smooth motion between points
- **Joint limits**: Respecting mechanical constraints
- **Safety interlocks**: Emergency stop integration

**Example test:**
```python
def test_forward_kinematics():
    arm = ArmController(simulate=True)
    
    # Test known joint configuration
    joints = [0, π/2, 0, 0]  # Home position
    expected_pos = [0.3, 0, 0.4]  # Expected end-effector position
    
    actual_pos = arm.forward_kinematics(joints)
    assert np.allclose(actual_pos, expected_pos, atol=1e-3)

def test_inverse_kinematics():
    arm = ArmController(simulate=True)
    
    target_pos = [0.3, 0.1, 0.3]
    joints = arm.inverse_kinematics(target_pos)
    
    # Verify solution works
    actual_pos = arm.forward_kinematics(joints)
    assert np.allclose(actual_pos, target_pos, atol=1e-3)
```

**Location:** `tests/test_arm.py`

### **test_drive.py** - Drive System Testing
Tests wheeled locomotion, motor control, and odometry.

**Key test areas:**
- **Velocity control**: Speed and direction accuracy
- **Odometry**: Position tracking accuracy
- **PID tuning**: Stable speed control
- **Motor limits**: Current and speed limits
- **Encoder feedback**: Wheel rotation sensing

**Example test:**
```python
def test_velocity_control():
    drive = DriveController(simulate=True)
    
    # Test forward motion
    drive.set_velocity(0.5, 0.0)  # 0.5 m/s forward
    time.sleep(1.0)
    
    # Check encoder feedback
    distance = drive.get_odometry()
    assert abs(distance - 0.5) < 0.1  # Within 10cm accuracy

def test_pid_response():
    drive = DriveController(simulate=True)
    
    # Test step response
    drive.set_velocity(1.0, 0.0)
    
    velocities = []
    for i in range(50):
        vel = drive.get_current_velocity()
        velocities.append(vel)
        time.sleep(0.02)
    
    # Check settling time and overshoot
    final_vel = np.mean(velocities[-10:])  # Last 200ms average
    assert abs(final_vel - 1.0) < 0.1
```

**Location:** `tests/test_drive.py`

### **test_sensors.py** - Sensor System Testing
Tests sensor interfaces, data processing, and sensor fusion.

**Key test areas:**
- **Sensor reading**: Raw data acquisition
- **Data filtering**: Noise reduction algorithms
- **Calibration**: Offset and scale corrections
- **Sensor fusion**: Combining multiple sensors
- **Error handling**: Faulty sensor detection

**Example test:**
```python
def test_imu_calibration():
    imu = IMU(simulate=True)
    
    # Test calibration application
    raw_accel = [0.01, 0.02, 9.85]  # Raw readings
    calibrated = imu.apply_calibration(raw_accel)
    
    # Should be close to [0, 0, 9.81] (gravity)
    expected = [0, 0, 9.81]
    assert np.allclose(calibrated, expected, atol=0.1)

def test_kalman_filter():
    kf = KalmanFilter()
    
    # Test prediction and update
    kf.predict()  # Time update
    measurement = [1.0, 0.5, 0.2]  # Position measurement
    kf.update(measurement)  # Measurement update
    
    state = kf.get_state()
    assert len(state) == 6  # Position + velocity (3D)
```

**Location:** `tests/test_sensors.py`

### **test_vision.py** - Vision System Testing
Tests camera interface, object detection, and tracking.

**Key test areas:**
- **Camera capture**: Image acquisition
- **Object detection**: Model inference accuracy
- **Coordinate transformation**: Pixel to robot coordinates
- **Tracking stability**: Object following over time
- **Performance**: Detection speed and reliability

**Example test:**
```python
def test_object_detection():
    detector = TrashDetector(model_path='models/vision/trash_detector.pt')
    
    # Create test image with known object
    test_image = create_test_image_with_trash()
    
    detections = detector.detect(test_image)
    
    # Should detect the test object
    assert len(detections) >= 1
    best_det = max(detections, key=lambda d: d['confidence'])
    assert best_det['confidence'] > 0.5
    assert best_det['class'] == 'plastic_bottle'

def test_coordinate_transform():
    vision = VisionSystem()
    
    # Test pixel to robot coordinate conversion
    pixel_coords = (320, 240)  # Center of 640x480 image
    depth = 1.0  # 1 meter away
    
    robot_coords = vision.pixel_to_robot(pixel_coords, depth)
    
    # Should be close to robot center at 1m forward
    expected = [1.0, 0.0, 0.0]  # X=1m, Y=0, Z=0
    assert np.allclose(robot_coords, expected, atol=0.1)
```

**Location:** `tests/test_vision.py`

### **test_safety.py** - Safety System Testing
Tests emergency stops, interlocks, and safety monitoring.

**Key test areas:**
- **E-stop activation**: Immediate system shutdown
- **Interlock checking**: Safety condition monitoring
- **Watchdog timing**: Heartbeat monitoring
- **Fault recovery**: Safe error handling
- **Safety overrides**: Emergency operation modes

**Example test:**
```python
def test_emergency_stop():
    safety = SafetySystem()
    robot = RobotSystem()
    
    # Normal operation
    robot.drive.set_velocity(0.5, 0.0)
    assert robot.drive.get_velocity() > 0
    
    # Trigger E-stop
    safety.emergency_stop()
    
    # Verify immediate stop
    assert robot.drive.get_velocity() == 0
    assert robot.arm.is_stopped()
    assert safety.is_emergency_active()

def test_safety_interlocks():
    safety = SafetyInterlocks()
    
    # Test joint limit interlock
    joint_pos = 180  # Over limit
    assert not safety.check_joint_limits(joint_pos)
    
    # Test velocity limit interlock
    velocity = 2.0  # Over limit
    assert not safety.check_velocity_limits(velocity)
    
    # Test combined interlocks
    state = {'joint_pos': 90, 'velocity': 0.5, 'obstacle': False}
    assert safety.check_all_interlocks(state)
```

**Location:** `tests/test_safety.py`

## Integration Tests (tests/integration/)

### **test_full_pickup.py** - Complete Pickup Workflow
Tests the entire trash pickup sequence from detection to disposal.

**Test flow:**
1. **Vision detection**: Locate trash object
2. **Path planning**: Navigate to object
3. **Arm positioning**: Move arm to pickup pose
4. **Gripper operation**: Grasp the object
5. **Return navigation**: Go to disposal area
6. **Object release**: Drop object
7. **Home position**: Return to ready state

**Example test:**
```python
def test_complete_pickup_sequence():
    robot = RobotSystem(simulate=True)
    
    # Setup test environment
    place_trash_at(robot, position=[1.0, 0.0, 0.1])
    
    # Execute pickup sequence
    success = robot.execute_pickup_sequence()
    
    # Verify success
    assert success
    assert robot.has_object_in_gripper()
    assert robot.at_disposal_area()
```

**Location:** `tests/integration/test_full_pickup.py`

## Test Fixtures and Mocks

### **conftest.py** - Shared Test Configuration
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_robot():
    """Mock robot for testing"""
    robot = Mock()
    robot.drive = Mock()
    robot.arm = Mock()
    robot.vision = Mock()
    return robot

@pytest.fixture
def test_config():
    """Standard test configuration"""
    return {
        'simulate': True,
        'log_level': 'DEBUG',
        'safety_enabled': False  # For testing
    }

@pytest.fixture(scope="session")
def hardware_setup():
    """Real hardware setup for integration tests"""
    if not pytest.config.getoption("--hardware"):
        pytest.skip("Hardware tests not enabled")
    
    # Setup real hardware
    robot = RobotSystem(simulate=False)
    yield robot
    robot.shutdown()
```

### **Mock Objects**
```python
def create_mock_sensor():
    """Mock sensor for testing"""
    sensor = Mock()
    sensor.get_reading.return_value = 42.0
    sensor.is_connected.return_value = True
    return sensor

def create_mock_motor():
    """Mock motor controller"""
    motor = Mock()
    motor.set_speed.side_effect = lambda s: None
    motor.get_position.return_value = 0.0
    return motor
```

## Debugging Test Failures

### **Common Test Issues**

**Issue: Import errors**
```
ImportError: No module named 'trashformer'
```
**Fix:**
```bash
# Add project to Python path
export PYTHONPATH="$PWD:$PYTHONPATH"
pytest tests/
```

**Issue: Hardware not available**
```
HardwareError: No motor controller found
```
**Fix:**
```bash
# Run simulation tests only
pytest -m "not hardware"

# Or use mock hardware
pytest --mock-hardware
```

**Issue: Test timeouts**
```
Failed: Timeout >30s
```
**Fix:**
```python
@pytest.mark.timeout(60)  # Increase timeout
def test_slow_operation():
    pass
```

**Issue: Flaky tests**
```
Test passed on run 1, failed on run 2
```
**Fix:**
```python
@pytest.mark.flaky(reruns=3)  # Retry failed tests
def test_unreliable_hardware():
    pass
```

### **Debugging Techniques**
```python
# Add debug prints
def test_problematic_function():
    result = some_function()
    print(f"Debug: result = {result}")  # Will show with -s flag
    assert result == expected

# Use debugger
def test_with_debugger():
    import pdb; pdb.set_trace()
    result = complex_function()
    assert result.correct

# Log detailed information
import logging
logging.basicConfig(level=logging.DEBUG)

def test_with_logging():
    logger = logging.getLogger(__name__)
    logger.debug("Starting test...")
    # Test code...
```

### **Test Isolation Issues**
```python
# Problem: Tests affect each other
class TestIsolated:
    def setup_method(self):
        # Reset state before each test
        reset_global_state()
    
    def teardown_method(self):
        # Clean up after each test
        cleanup_resources()
```

## Test Coverage and Quality

### **Coverage Analysis**
```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# Check coverage thresholds
pytest --cov=. --cov-fail-under=80

# Coverage by module
pytest --cov=arm --cov=drive --cov-report=term-missing
```

### **Code Quality Checks**
```bash
# Lint test code
flake8 tests/

# Type checking
mypy tests/

# Security scanning
bandit tests/
```

### **Performance Testing**
```python
import time

def test_performance():
    start = time.time()
    for i in range(1000):
        result = expensive_function()
    end = time.time()
    
    duration = end - start
    assert duration < 1.0  # Must complete within 1 second
```

## Continuous Integration

### **GitHub Actions Example**
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### **Hardware Testing**
```bash
# Test on actual robot
ssh robot@trashformer.local "cd /home/robot && pytest tests/ --hardware"

# Test with different configurations
pytest tests/ --config=config/production.yaml
pytest tests/ --config=config/development.yaml
```

## Best Practices

### **Test Organization**
- One test file per module
- Descriptive test names
- Logical grouping with classes
- Clear setup/teardown

### **Test Quality**
- Test both success and failure cases
- Use realistic test data
- Avoid testing implementation details
- Keep tests fast and reliable

### **Mocking Strategy**
- Mock external dependencies
- Use fixtures for common setup
- Avoid over-mocking (test real code when possible)
- Verify mock interactions

### **Test Maintenance**
- Update tests when code changes
- Remove obsolete tests
- Add tests for bug fixes
- Review test coverage regularly

## Where to Find Everything

**Test files:** `tests/test_*.py`
- `test_arm.py`: Arm system tests
- `test_drive.py`: Drive system tests
- `test_sensors.py`: Sensor system tests
- `test_safety.py`: Safety system tests
- `test_vision.py`: Vision system tests

**Integration tests:** `tests/integration/`
- `test_full_pickup.py`: Complete pickup workflow

**Test configuration:** `tests/conftest.py`
- Shared fixtures and configuration

**Test reports:** `htmlcov/` (coverage), `report.html` (test results)

**Test tools:** `tools/run_tests.py` - Custom test runner

**CI/CD:** `.github/workflows/tests.yml` - Automated testing
