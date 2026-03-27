"""
DUAL ROBOCLAW SETUP GUIDE
==========================

Hardware: 2x RoboClaw motor controllers + goBILDA Servo PDB
- RoboClaw 1: Left tracks (2 motors)
- RoboClaw 2: Right tracks (2 motors)
- Servo PDB: Power distribution only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WIRING DIAGRAM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────┐
│  Raspberry Pi 4                                                 │
│                                                                 │
│  GPIO 14 (TX) ──┬──→ RoboClaw 1 S1 (RX)                       │
│                 └──→ RoboClaw 2 S1 (RX)                       │
│                                                                 │
│  GPIO 15 (RX) ──┬──← RoboClaw 1 S2 (TX)                       │
│                 └──← RoboClaw 2 S2 (TX)                       │
│                                                                 │
│  GND ───────────┴──→ RoboClaw 1 & 2 GND                       │
└─────────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│  RoboClaw 1 (Left Tracks) - Address 0x80                       │
│                                                                 │
│  M1 ──→ Left Front Motor                                       │
│  M2 ──→ Left Rear Motor                                        │
│                                                                 │
│  B+ / B- ← Battery (via PDB)                                   │
│  S1 (RX) ← Pi GPIO 14 (TX)                                     │
│  S2 (TX) → Pi GPIO 15 (RX)                                     │
│  GND ← Pi GND                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  RoboClaw 2 (Right Tracks) - Address 0x81                      │
│                                                                 │
│  M1 ──→ Right Front Motor                                      │
│  M2 ──→ Right Rear Motor                                       │
│                                                                 │
│  B+ / B- ← Battery (via PDB)                                   │
│  S1 (RX) ← Pi GPIO 14 (TX)                                     │
│  S2 (TX) → Pi GPIO 15 (RX)                                     │
│  GND ← Pi GND                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  goBILDA Servo PDB (Power Distribution Board)                  │
│                                                                 │
│  Battery Input ← Main battery                                  │
│  Output 1 → RoboClaw 1 (B+/B-)                                │
│  Output 2 → RoboClaw 2 (B+/B-)                                │
│  5V/6V Outputs → Servos (arm control)                         │
└─────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROBOCLAW CONFIGURATION (Motion Studio)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connect each RoboClaw to computer via USB and configure:

RoboClaw 1 (Left):
  General Settings:
    - Control Mode: Packet Serial
    - Multi-Unit Mode: ENABLED ✓
  
  Serial Settings:
    - Address: 128 (0x80)
    - Baudrate: 38400
  
  Motor Settings:
    - M1 & M2: Direction as needed for left tracks

RoboClaw 2 (Right):
  General Settings:
    - Control Mode: Packet Serial
    - Multi-Unit Mode: ENABLED ✓
  
  Serial Settings:
    - Address: 129 (0x81)
    - Baudrate: 38400
  
  Motor Settings:
    - M1 & M2: Direction as needed for right tracks

CRITICAL: Both RoboClaws must have different addresses!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RASPBERRY PI CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ENABLE SERIAL PORT:
   sudo raspi-config
   → Interface Options
   → Serial Port
   → "Would you like a login shell accessible over serial?" NO
   → "Would you like the serial port hardware enabled?" YES
   
2. DISABLE BLUETOOTH (frees up /dev/ttyAMA0):
   sudo nano /boot/config.txt
   Add: dtoverlay=disable-bt
   sudo systemctl disable hciuart
   sudo reboot

3. INSTALL ROBOCLAW LIBRARY:
   pip3 install roboclaw_3 --break-system-packages

4. TEST SERIAL PORT:
   ls -l /dev/ttyS0  # Should exist
   ls -l /dev/ttyAMA0  # Should exist after disabling BT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WIRING DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Serial Connection (Multi-Unit Mode):
  Pi GPIO 14 (TX) ─┬─→ RoboClaw 1 S1
                   └─→ RoboClaw 2 S1
  
  Pi GPIO 15 (RX) ─┬─← RoboClaw 1 S2
                   └─← RoboClaw 2 S2
  
  Pi GND ──────────┴─→ Both RoboClaw GNDs

Motor Connections:
  Left RoboClaw (0x80):
    M1A/M1B → Left Front Motor
    M2A/M2B → Left Rear Motor
  
  Right RoboClaw (0x81):
    M1A/M1B → Right Front Motor
    M2A/M2B → Right Rear Motor

Power:
  Battery → PDB → RoboClaws B+/B-
  Common ground between all components!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. TEST ROBOCLAW CONNECTION:
   cd ~/trashformer
   python3 -c "
from drive.roboclaw_controller import DualRoboClawController
import time

rc = DualRoboClawController(port='/dev/ttyS0', baudrate=38400, simulate=False)
time.sleep(1)
rc.close()
"

   Expected: See firmware versions for both RoboClaws

2. TEST MOTORS (robot on blocks!):
   python3 -c "
from drive.roboclaw_controller import DualRoboClawController
import time

rc = DualRoboClawController(simulate=False)

print('Forward')
rc.set_motors(0.3, 0.3)
time.sleep(2)

print('Stop')
rc.stop()
time.sleep(1)

print('Rotate left')
rc.set_motors(-0.3, 0.3)
time.sleep(2)

print('Stop')
rc.stop()
rc.close()
"

3. TEST WITH KEYBOARD TELEOP:
   cd ~/trashformer/tools
   python3 teleop_keyboard.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOVEMENT LOGIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Forward (all 4 motors ON):
  Left RoboClaw:  M1 forward, M2 forward
  Right RoboClaw: M1 forward, M2 forward
  Result: All 4 motors drive forward ✓

Backward (all 4 motors ON):
  Left RoboClaw:  M1 reverse, M2 reverse
  Right RoboClaw: M1 reverse, M2 reverse
  Result: All 4 motors drive backward ✓

Turn Left (differential):
  Left RoboClaw:  M1 reverse, M2 reverse
  Right RoboClaw: M1 forward, M2 forward
  Result: Left tracks reverse, right tracks forward → Turn left ↺

Turn Right (differential):
  Left RoboClaw:  M1 forward, M2 forward
  Right RoboClaw: M1 reverse, M2 reverse
  Result: Left tracks forward, right tracks reverse → Turn right ↻

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIGURATION FILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

config/default.yaml:

drive:
  motor_controller:
    port: "/dev/ttyS0"        # or /dev/ttyAMA0
    baudrate: 38400
    left_address: 0x80        # 128
    right_address: 0x81       # 129

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: "Failed to connect to RoboClaw"
→ Check serial wiring (TX → RX, RX → TX)
→ Verify baudrate matches (38400)
→ Check addresses (0x80, 0x81)
→ Ensure Multi-Unit mode enabled
→ Try /dev/ttyAMA0 instead of /dev/ttyS0

Problem: Motors don't move
→ Check motor power (B+/B-)
→ Verify motor connections
→ Check for error LEDs on RoboClaw
→ Test each RoboClaw independently

Problem: Wrong motor direction
→ Swap motor wires (M1A ↔ M1B)
→ OR change direction in Motion Studio
→ OR invert in code (multiply speed by -1)

Problem: Only one RoboClaw works
→ Check addresses are different (0x80 vs 0x81)
→ Verify both connected to serial bus
→ Check ground connections

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(__doc__)