#!/usr/bin/env python3
"""
main.py — Robot entry point (Week 1)

Goals:
- Load config.yaml (single source of truth)
- Print a startup summary (so debugging is easy)
- Sanity-check key interfaces:
    * I2C presence for PCA9685 (servo board)
    * Serial presence for Sabertooth (track motor driver)
"""

from __future__ import annotations

from pathlib import Path
import yaml

# Optional dependencies; handled gracefully if not installed yet
try:
    from smbus2 import SMBus
except Exception:
    SMBus = None

try:
    import serial
except Exception:
    serial = None


CONFIG_PATH = Path(__file__).with_name("config.yaml")


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError("config.yaml did not parse into a dictionary.")
    return cfg


def parse_hex_int(value, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        return int(v, 16) if v.startswith("0x") else int(v)
    return default


def i2c_probe(address: int, bus_num: int = 1) -> bool:
    """Return True if a device ACKs at address on I2C bus."""
    if SMBus is None:
        print("  [I2C] smbus2 not installed (skipping I2C check).")
        return False
    try:
        with SMBus(bus_num) as bus:
            bus.write_quick(address)
        return True
    except Exception:
        return False


def serial_probe(port: str, baud: int) -> bool:
    """Return True if we can open the serial port."""
    if serial is None:
        print("  [SERIAL] pyserial not installed (skipping serial check).")
        return False
    try:
        with serial.Serial(port=port, baudrate=baud, timeout=1) as ser:
            return bool(ser.is_open)
    except Exception:
        return False


def print_startup_summary(cfg: dict) -> None:
    robot_name = cfg.get("robot", {}).get("name", "UnnamedRobot")
    loop_rate = cfg.get("robot", {}).get("loop_rate_hz", "unknown")

    print("\n==============================")
    print(f" Robot Startup: {robot_name}")
    print("==============================")
    print(f"Loop rate: {loop_rate} Hz")

    # Drive config
    drive = cfg.get("drive", {})
    print("\n[Drive]")
    print(f"  Type: {drive.get('type')}")
    print(f"  Controller: {drive.get('controller')}")
    print(f"  Serial port: {drive.get('serial_port')}")
    print(f"  Baudrate: {drive.get('baudrate')}")

    # Servo config
    servos = cfg.get("servos", {})
    i2c_addr = parse_hex_int(servos.get("i2c_address"), 0x40)
    print("\n[Servos]")
    print(f"  Controller: {servos.get('controller')}")
    print(f"  I2C address: 0x{i2c_addr:02X}")
    print(f"  PWM freq: {servos.get('pwm_frequency')} Hz")

    # Arm config (single-arm-first)
    arms = cfg.get("arms", {})
    enabled_arms = int(arms.get("enabled_arms", 1))
    print("\n[Arms]")
    print(f"  Enabled arms: {enabled_arms}")

    # Print arm joint mapping for enabled arms only
    for idx in range(1, enabled_arms + 1):
        arm_key = f"arm_{idx}"
        arm_cfg = arms.get(arm_key, {})
        arm_name = arm_cfg.get("name", arm_key)
        joints = arm_cfg.get("joints", {})
        print(f"  {arm_key} ({arm_name}): {len(joints)} joints")
        for jname, jcfg in joints.items():
            ch = jcfg.get("channel", "n/a")
            print(f"    - {jname}: channel {ch}")

    # Sensors config
    sensors = cfg.get("sensors", {})
    tof = sensors.get("tof", {})
    imu = sensors.get("imu", {})
    ultra = sensors.get("ultrasonic", {})
    limits = sensors.get("limit_switches", {})

    print("\n[Sensors]")
    print(f"  TOF addr: 0x{parse_hex_int(tof.get('i2c_address'), 0x29):02X}")
    print(f"  IMU: {imu.get('type')} addr 0x{parse_hex_int(imu.get('i2c_address'), 0x68):02X}")
    print(f"  Ultrasonic trig/echo GPIO: {ultra.get('trigger_gpio')}/{ultra.get('echo_gpio')}")
    if limits:
        for k, v in limits.items():
            print(f"  Limit switch '{k}': GPIO {v.get('gpio')}")
    else:
        print("  Limit switches: none listed")


def main() -> int:
    # Load config
    try:
        cfg = load_config(CONFIG_PATH)
    except Exception as e:
        print(f"ERROR: Could not load config.yaml: {e}")
        return 1

    print_startup_summary(cfg)

    print("\n[Checks]")

    # I2C PCA9685 probe
    servos = cfg.get("servos", {})
    pca_addr = parse_hex_int(servos.get("i2c_address"), 0x40)
    pca_ok = i2c_probe(pca_addr, bus_num=1)
    print(f"  PCA9685 @ 0x{pca_addr:02X}: {'FOUND' if pca_ok else 'NOT FOUND'}")

    # Serial Sabertooth probe
    drive = cfg.get("drive", {})
    port = drive.get("serial_port", "/dev/ttyUSB0")
    baud = int(drive.get("baudrate", 9600))
    sab_ok = serial_probe(port, baud)
    print(f"  Sabertooth serial ({port} @ {baud}): {'OPENED' if sab_ok else 'FAILED'}")

    # Decide failure behavior (Week 1): fail only if libs exist and probe fails
    if SMBus is not None and not pca_ok:
        print("\nERROR: PCA9685 not detected on I2C.")
        print("Fix: enable I2C, check SDA/SCL wiring, ensure PCA9685 has power + common ground.")
        return 2

    if serial is not None and not sab_ok:
        print("\nERROR: Sabertooth serial port not opening.")
        print("Fix: check USB/serial adapter, correct /dev/tty* device, permissions, baudrate.")
        return 3

    print("\n✅ Startup checks complete.")
    print("Next: run safe test scripts in /tools (servos first, then motors).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
