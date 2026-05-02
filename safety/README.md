# Safety Module

This module implements safety systems and fail-safe mechanisms to protect the robot, operators, and bystanders.

## Files

- **estop.py** - Emergency stop (E-stop) implementation
- **interlocks.py** - Safety interlocks and lockouts
- **watchdog.py** - Watchdog timer for hardware health monitoring

## Emergency Stop (E-Stop)

The E-stop system provides:
- Hardware emergency stop button input
- Software emergency stop command
- Immediate motor shutdown
- System state freezing
- Communication of E-stop state

```python
from safety.estop import EmergencyStop

estop = EmergencyStop()
if estop.is_triggered():
    # Perform safe shutdown
    pass
```

## Interlocks

Safety interlocks prevent dangerous operations:
- **Arm interlock** - Prevents arm movement when gripper isn't secure
- **Motion interlock** - Prevents motion during arm pickup
- **Sensor interlock** - Requires sensor health before autonomous operation
- **Power interlock** - Prevents operation on low battery

```python
from safety.interlocks import SafetyInterlocks

interlocks = SafetyInterlocks()
if interlocks.can_move_arm():
    arm.move()
else:
    logger.warning("Arm movement prevented by interlock")
```

## Watchdog

Hardware watchdog timer for fault detection:
- Monitors system health
- Detects software hangs
- Triggers automatic shutdown on failure
- Logs fault information

```python
from safety.watchdog import Watchdog

watchdog = Watchdog(timeout_seconds=5.0)
watchdog.start()
# ... periodic operations ...
watchdog.heartbeat()  # Reset watchdog timer
watchdog.stop()
```

## Safety Critical Operations

High-risk operations include:
- Motor movement at high speed
- Arm motion with heavy load
- Autonomous navigation in crowded areas
- Battery charging

All require safety interlocks to be verified before execution.

## Operator Safety

- E-stop button must be easily accessible
- Safety stops should be tested regularly
- Communication of error states to operator
- Status indicators (lights, sounds)
- Manual mode fallback

## System Integration

Safety systems are checked:
- Before each subsystem command
- In the main control loop (watchdog)
- During initialization (sensor health)
- On shutdown (safe state verification)

## Testing Safety Systems

Use the safety test scripts:
```bash
python tests/test_safety.py
```

This verifies:
- E-stop functionality
- Interlock conditions
- Watchdog operation
- Emergency procedures
