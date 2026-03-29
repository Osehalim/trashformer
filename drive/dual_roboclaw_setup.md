# DUAL ROBOCLAW USB SETUP GUIDE

Hardware: 2x RoboClaw motor controllers + goBILDA Servo PDB
- RoboClaw 1: Left tracks (2 motors)
- RoboClaw 2: Right tracks (2 motors)
- Servo PDB: Power distribution only
- Raspberry Pi connects to each RoboClaw by USB

---

## WIRING DIAGRAM

```text
┌─────────────────────────────────────────────────────────────────┐
│  Raspberry Pi                                                  │
│                                                                 │
│  USB Port 1 ─────────────→ RoboClaw 1 micro-USB               │
│  USB Port 2 ─────────────→ RoboClaw 2 micro-USB               │
└─────────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│  RoboClaw 1 (Left Tracks)                                      │
│                                                                 │
│  M1 ──→ Left Front Motor                                       │
│  M2 ──→ Left Rear Motor                                        │
│  B+ / B- ← Battery (via PDB)                                   │
│  USB ← Pi USB port                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  RoboClaw 2 (Right Tracks)                                     │
│                                                                 │
│  M1 ──→ Right Front Motor                                      │
│  M2 ──→ Right Rear Motor                                       │
│  B+ / B- ← Battery (via PDB)                                   │
│  USB ← Pi USB port                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  goBILDA Servo PDB (Power Distribution Board)                  │
│                                                                 │
│  Battery Input ← Main battery                                  │
│  Output 1 → RoboClaw 1 (B+/B-)                                 │
│  Output 2 → RoboClaw 2 (B+/B-)                                 │
│  5V/6V Outputs → Servos (arm control)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## IMPORTANT NOTES

- USB is for communication only.
- Motors still need external battery power through B+/B-.
- You do not need Pi TX/RX GPIO wiring in USB mode.
- Each RoboClaw shows up as its own serial device, usually `/dev/ttyACM0` and `/dev/ttyACM1`.
- On USB, the controllers are physically separate, so using the same address on both is fine. This code still allows separate addresses if you want them.

---

## ROBOCLAW CONFIGURATION (Motion Studio)

Connect each RoboClaw to a computer via USB and configure:

### RoboClaw 1 (Left)
- Control Mode: Packet Serial
- Baudrate: 38400
- Address: 128 (0x80)

### RoboClaw 2 (Right)
- Control Mode: Packet Serial
- Baudrate: 38400
- Address: 128 (0x80) or 129 (0x81)

Recommended for this code:
- Left address: `0x80`
- Right address: `0x80`

If you prefer unique addresses, that also works.

---

## RASPBERRY PI CONFIGURATION

### 1. Install RoboClaw library

```bash
pip3 install roboclaw_3 --break-system-packages
```

### 2. Plug in both controllers

Then check:

```bash
ls /dev/ttyACM*
```

Expected result:

```bash
/dev/ttyACM0
/dev/ttyACM1
```

### 3. Optional: identify which is left and right

```bash
dmesg | grep ttyACM
```

If the ports swap after reboot, use udev rules later for fixed names.

---

## CONFIGURATION FILE

Update `config/default.yaml` like this:

```yaml
drive:
  motor_controller:
    mode: "usb"
    left_port: "/dev/ttyACM0"
    right_port: "/dev/ttyACM1"
    baudrate: 38400
    left_address: 0x80
    right_address: 0x80
```

If you decide to keep different addresses:

```yaml
drive:
  motor_controller:
    mode: "usb"
    left_port: "/dev/ttyACM0"
    right_port: "/dev/ttyACM1"
    baudrate: 38400
    left_address: 0x80
    right_address: 0x81
```

---

## TESTING

### 1. Test RoboClaw connection

```bash
cd ~/trashformer
python3 -c "
from drive.roboclaw_controller import DualRoboClawController
import time

rc = DualRoboClawController(
    mode='usb',
    left_port='/dev/ttyACM0',
    right_port='/dev/ttyACM1',
    left_address=0x80,
    right_address=0x80,
    baudrate=38400,
    simulate=False,
)
time.sleep(1)
rc.close()
"
```

Expected: see firmware version logs for both controllers.

### 2. Test motors (robot on blocks)

```bash
python3 -c "
from drive.roboclaw_controller import DualRoboClawController
import time

rc = DualRoboClawController(
    mode='usb',
    left_port='/dev/ttyACM0',
    right_port='/dev/ttyACM1',
    simulate=False,
)

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
```

### 3. Test with keyboard teleop

```bash
cd ~/trashformer/tools
python3 teleop_keyboard.py
```

---

## MOVEMENT LOGIC

### Forward
- Left RoboClaw: M1 forward, M2 forward
- Right RoboClaw: M1 forward, M2 forward
- Result: all 4 motors drive forward

### Backward
- Left RoboClaw: M1 reverse, M2 reverse
- Right RoboClaw: M1 reverse, M2 reverse
- Result: all 4 motors drive backward

### Turn Left
- Left RoboClaw: M1 reverse, M2 reverse
- Right RoboClaw: M1 forward, M2 forward
- Result: left tracks reverse, right tracks forward

### Turn Right
- Left RoboClaw: M1 forward, M2 forward
- Right RoboClaw: M1 reverse, M2 reverse
- Result: left tracks forward, right tracks reverse

---

## TROUBLESHOOTING

### Problem: one controller does not connect
- Check the USB cable.
- Check `ls /dev/ttyACM*`.
- Verify the RoboClaw is powered.
- Confirm baudrate matches Motion Studio.
- Try swapping cables and USB ports.

### Problem: ports swap after reboot
- This is common with `/dev/ttyACM0` and `/dev/ttyACM1`.
- Use udev rules for fixed names later, such as `/dev/roboclaw_left` and `/dev/roboclaw_right`.

### Problem: motors do not move
- Check battery power on B+/B-.
- Verify motor wiring.
- Check error LEDs on RoboClaw.
- Test each controller separately.

### Problem: wrong motor direction
- Swap motor wires (M1A ↔ M1B).
- Or change motor direction in Motion Studio.
- Or invert speed in code.
