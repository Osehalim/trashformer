#!/usr/bin/env python3
"""
tools/test_one_servo_pca.py — Non-interactive single servo test via PCA9685

Moves ONE channel: center -> small left -> center -> small right -> center

Usage:
  python3 -m tools.test_one_servo_pca --channel 0
  python3 -m tools.test_one_servo_pca --channel 1 --min_us 1000 --max_us 2000
"""

from __future__ import annotations

import argparse
import time

from utils.config_loader import load_config
from utils.logger import setup_logging
from arm.pca9685_driver import PCA9685


def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", type=int, default=0, help="PCA9685 channel (0-15)")
    parser.add_argument("--center_us", type=int, default=1500, help="Center pulse (us)")
    parser.add_argument("--delta_us", type=int, default=150, help="Move amount from center (us)")
    parser.add_argument("--min_us", type=int, default=500, help="Hard min clamp (us)")
    parser.add_argument("--max_us", type=int, default=2500, help="Hard max clamp (us)")
    parser.add_argument("--hold", type=float, default=0.8, help="Hold seconds at each position")
    args = parser.parse_args()

    i2c_bus = int(cfg.get("hardware.i2c_bus", 1))
    i2c_addr = int(cfg.get("hardware.i2c_address", 0x40))
    freq = int(cfg.get("arm.pwm_frequency", 50))

    ch = args.channel
    center = clamp(args.center_us, args.min_us, args.max_us)
    a1 = clamp(center - args.delta_us, args.min_us, args.max_us)
    a2 = clamp(center + args.delta_us, args.min_us, args.max_us)

    print("\n=== Single Servo Test (PCA9685) ===")
    print(f"I2C bus: {i2c_bus}  addr: 0x{i2c_addr:02X}  freq: {freq}Hz")
    print(f"Channel: {ch}")
    print(f"Pulses: {center} -> {a1} -> {center} -> {a2} -> {center}")
    print("CTRL+C to stop.\n")

    pwm = PCA9685(i2c_bus=i2c_bus, address=i2c_addr, frequency=freq, simulate=False)

    try:
        for pulse in (center, a1, center, a2, center):
            pwm.set_pulse_width(ch, int(pulse))
            print(f"Set channel {ch} to {pulse} us")
            time.sleep(args.hold)

        print("\n✅ Done.")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 2

    finally:
        try:
            pwm.set_pwm(ch, 0, 0)  # disable channel
        except Exception:
            pass
        pwm.close()


if __name__ == "__main__":
    raise SystemExit(main())