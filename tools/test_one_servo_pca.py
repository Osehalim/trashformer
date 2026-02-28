#!/usr/bin/env python3
"""
tools/test_one_servo_pca.py — Large-movement single servo test via PCA9685

Moves ONE channel:
  center -> far left -> center -> far right -> center

Usage:
  python3 -m tools.test_one_servo_pca --channel 0
"""

from __future__ import annotations

import argparse
import time

from utils.config_loader import load_config
from utils.logger import setup_logging
from arm.pca9685_driver import PCA9685


def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def sweep(pwm, ch, start, end, step, delay):
    if start < end:
        p = start
        while p <= end:
            pwm.set_pulse_width(ch, p)
            time.sleep(delay)
            p += step
    else:
        p = start
        while p >= end:
            pwm.set_pulse_width(ch, p)
            time.sleep(delay)
            p -= step


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--center_us", type=int, default=1500)
    parser.add_argument("--delta_us", type=int, default=400)  # MUCH LARGER
    parser.add_argument("--min_us", type=int, default=800)    # safer real limits
    parser.add_argument("--max_us", type=int, default=2200)
    parser.add_argument("--step", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.02)
    parser.add_argument("--hold", type=float, default=1.0)
    args = parser.parse_args()

    i2c_bus = int(cfg.get("hardware.i2c_bus", 1))
    i2c_addr = int(cfg.get("hardware.i2c_address", 0x40))
    freq = int(cfg.get("arm.pwm_frequency", 50))

    ch = args.channel

    center = clamp(args.center_us, args.min_us, args.max_us)
    left = clamp(center - args.delta_us, args.min_us, args.max_us)
    right = clamp(center + args.delta_us, args.min_us, args.max_us)

    print("\n=== Large Servo Movement Test ===")
    print(f"Channel: {ch}")
    print(f"Center: {center} us")
    print(f"Left:   {left} us")
    print(f"Right:  {right} us")
    print("CTRL+C to stop.\n")

    pwm = PCA9685(i2c_bus=i2c_bus, address=i2c_addr, frequency=freq, simulate=False)

    try:
        # Go to center
        pwm.set_pulse_width(ch, center)
        time.sleep(args.hold)

        # Sweep to left
        sweep(pwm, ch, center, left, args.step, args.delay)
        time.sleep(args.hold)

        # Sweep back to center
        sweep(pwm, ch, left, center, args.step, args.delay)
        time.sleep(args.hold)

        # Sweep to right
        sweep(pwm, ch, center, right, args.step, args.delay)
        time.sleep(args.hold)

        # Sweep back to center
        sweep(pwm, ch, right, center, args.step, args.delay)
        time.sleep(args.hold)

        print("\n✅ Done.")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 2

    finally:
        try:
            pwm.set_pwm(ch, 0, 0)
        except Exception:
            pass
        pwm.close()


if __name__ == "__main__":
    raise SystemExit(main())