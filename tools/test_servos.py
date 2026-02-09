#!/usr/bin/env python3
"""
tools/test_servos.py — SAFE servo smoke test

What it does:
- Loads config.yaml
- Initializes PCA9685 on I2C
- Moves ONE joint (arm_1 shoulder) by a small delta
- Returns to safe angle

Safety rules:
- Keep the arm clear of anything it can hit.
- Use a proper 5–6V servo power supply (NOT the Pi 5V pin).
- Ensure common ground between servo power and Pi ground.
"""

from __future__ import annotations

import time
from pathlib import Path
import yaml

from smbus2 import SMBus

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_hex_int(value, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        return int(v, 16) if v.startswith("0x") else int(v)
    return default


class PCA9685:
    """Minimal PCA9685 driver for servo testing."""

    MODE1 = 0x00
    PRESCALE = 0xFE
    LED0_ON_L = 0x06

    def __init__(self, bus: SMBus, address: int = 0x40):
        self.bus = bus
        self.address = address

    def write8(self, reg: int, value: int) -> None:
        self.bus.write_byte_data(self.address, reg, value & 0xFF)

    def read8(self, reg: int) -> int:
        return self.bus.read_byte_data(self.address, reg)

    def set_pwm_freq(self, freq_hz: float) -> None:
        # PCA9685 internal oscillator default ~25MHz
        # prescale = round(25_000_000 / (4096 * freq) - 1)
        prescale_val = int(round(25_000_000.0 / (4096.0 * freq_hz) - 1.0))

        old_mode = self.read8(self.MODE1)
        sleep_mode = (old_mode & 0x7F) | 0x10  # sleep
        self.write8(self.MODE1, sleep_mode)
        self.write8(self.PRESCALE, prescale_val)
        self.write8(self.MODE1, old_mode)
        time.sleep(0.005)
        self.write8(self.MODE1, old_mode | 0x80)  # restart

    def set_pwm(self, channel: int, on: int, off: int) -> None:
        reg = self.LED0_ON_L + 4 * channel
        self.write8(reg + 0, on & 0xFF)
        self.write8(reg + 1, (on >> 8) & 0xFF)
        self.write8(reg + 2, off & 0xFF)
        self.write8(reg + 3, (off >> 8) & 0xFF)

    def set_servo_pulse_us(self, channel: int, pulse_us: int, pwm_freq_hz: float) -> None:
        # Convert microseconds to PCA9685 "tick" (0-4095) at given PWM freq
        period_us = 1_000_000.0 / pwm_freq_hz
        ticks = int(round((pulse_us / period_us) * 4096.0))
        ticks = max(0, min(4095, ticks))
        self.set_pwm(channel, 0, ticks)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def angle_to_pulse_us(angle: float, min_angle: float, max_angle: float, min_pulse: int, max_pulse: int) -> int:
    # Linear map angle -> pulse width
    ratio = (angle - min_angle) / (max_angle - min_angle) if max_angle != min_angle else 0.5
    ratio = clamp(ratio, 0.0, 1.0)
    return int(round(min_pulse + ratio * (max_pulse - min_pulse)))


def main() -> int:
    cfg = load_config(CONFIG_PATH)

    servos_cfg = cfg.get("servos", {})
    pca_addr = parse_hex_int(servos_cfg.get("i2c_address"), 0x40)
    pwm_freq = float(servos_cfg.get("pwm_frequency", 50))

    pulse_cfg = servos_cfg.get("pulse_width", {})
    global_min_pulse = int(pulse_cfg.get("min", 500))
    global_max_pulse = int(pulse_cfg.get("max", 2500))

    arms_cfg = cfg.get("arms", {})
    enabled_arms = int(arms_cfg.get("enabled_arms", 1))
    if enabled_arms < 1:
        print("No arms enabled in config.yaml (enabled_arms < 1).")
        return 1

    arm1 = arms_cfg.get("arm_1", {})
    joints = arm1.get("joints", {})
    if "shoulder" not in joints:
        print("config.yaml is missing arms.arm_1.joints.shoulder")
        return 1

    shoulder = joints["shoulder"]
    ch = int(shoulder["channel"])
    min_angle = float(shoulder.get("min_angle", 0))
    max_angle = float(shoulder.get("max_angle", 180))
    safe_angle = float(shoulder.get("safe_angle", 90))

    # Small safe movement
    delta = 10.0
    a1 = clamp(safe_angle - delta, min_angle, max_angle)
    a2 = clamp(safe_angle + delta, min_angle, max_angle)

    print("\n=== Servo Test (SAFE) ===")
    print(f"PCA9685 addr: 0x{pca_addr:02X}, freq: {pwm_freq} Hz")
    print(f"Testing arm_1 shoulder on channel {ch}")
    print(f"Angles: {a1} -> {safe_angle} -> {a2} -> {safe_angle}")
    print("If anything looks wrong, CTRL+C immediately.\n")

    try:
        with SMBus(1) as bus:
            pca = PCA9685(bus, pca_addr)
            pca.set_pwm_freq(pwm_freq)

            def go(angle: float) -> None:
                pulse = angle_to_pulse_us(angle, min_angle, max_angle, global_min_pulse, global_max_pulse)
                pca.set_servo_pulse_us(ch, pulse, pwm_freq)
                print(f"  Moved to {angle:.1f}° (pulse {pulse} us)")
                time.sleep(0.8)

            # Start at safe
            go(safe_angle)
            # Sweep small
            go(a1)
            go(safe_angle)
            go(a2)
            go(safe_angle)

        print("\n✅ Servo test completed.")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user (CTRL+C).")
        return 2
    except Exception as e:
        print(f"\nERROR: Servo test failed: {e}")
        print("Common fixes: enable I2C, check SDA/SCL wiring, power servos separately, share ground.")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
