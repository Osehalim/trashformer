#!/usr/bin/env python3
"""
tools/test_one_servo_pca.py — Single servo test via PCA9685

Tests a single servo by moving through its range.

Usage:
  # Test shoulder (500-1500μs range)
  python3 tools/test_one_servo_pca.py --channel 0 --servo shoulder
  
  # Test elbow (1000-2000μs range)
  python3 tools/test_one_servo_pca.py --channel 1 --servo elbow
  
  # Test gripper (500-2500μs range)
  python3 tools/test_one_servo_pca.py --channel 2 --servo gripper
  
  # Custom range
  python3 tools/test_one_servo_pca.py --channel 0 --min 500 --max 1500
"""

from __future__ import annotations

import argparse
import time
from utils.config_loader import load_config
from utils.logger import setup_logging, get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)


def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def sweep(pwm, ch, start, end, step, delay):
    """Sweep servo from start to end pulse width."""
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

    parser = argparse.ArgumentParser(description="Test a single servo")
    parser.add_argument("--channel", type=int, default=0, help="PCA9685 channel (0-15)")
    parser.add_argument("--servo", type=str, choices=['shoulder', 'elbow', 'gripper'], 
                       help="Servo type (sets pulse range automatically)")
    parser.add_argument("--min", type=int, help="Min pulse width (μs)")
    parser.add_argument("--max", type=int, help="Max pulse width (μs)")
    parser.add_argument("--step", type=int, default=10, help="Step size (μs)")
    parser.add_argument("--delay", type=float, default=0.02, help="Delay between steps (sec)")
    parser.add_argument("--hold", type=float, default=1.0, help="Hold time at endpoints (sec)")
    args = parser.parse_args()

    # Get PCA9685 settings
    i2c_addr = int(cfg.get("arm.i2c_address", 0x40))
    freq = int(cfg.get("arm.pwm_frequency", 50))
    ch = args.channel

    # Determine pulse range
    if args.servo:
        # Use servo-specific range from config
        if args.servo == 'shoulder':
            min_pulse = int(cfg.get("arm.shoulder.min_pulse", 500))
            max_pulse = int(cfg.get("arm.shoulder.max_pulse", 1500))
        elif args.servo == 'elbow':
            min_pulse = int(cfg.get("arm.elbow.min_pulse", 1000))
            max_pulse = int(cfg.get("arm.elbow.max_pulse", 2000))
        elif args.servo == 'gripper':
            min_pulse = int(cfg.get("arm.gripper.min_pulse", 500))
            max_pulse = int(cfg.get("arm.gripper.max_pulse", 2500))
    elif args.min and args.max:
        # Use custom range
        min_pulse = args.min
        max_pulse = args.max
    else:
        logger.error("Must specify either --servo or both --min and --max")
        return 1

    center = (min_pulse + max_pulse) // 2

    print("\n" + "="*60)
    print("SINGLE SERVO TEST")
    print("="*60)
    print(f"Channel:     {ch}")
    print(f"Servo type:  {args.servo if args.servo else 'custom'}")
    print(f"Min pulse:   {min_pulse}μs")
    print(f"Center:      {center}μs")
    print(f"Max pulse:   {max_pulse}μs")
    print(f"Step size:   {args.step}μs")
    print(f"Delay:       {args.delay}s")
    print("\nSequence:")
    print("  1. Move to center")
    print("  2. Sweep to min")
    print("  3. Sweep back to center")
    print("  4. Sweep to max")
    print("  5. Sweep back to center")
    print("\nCTRL+C to stop.")
    print("="*60 + "\n")

    pwm = PCA9685(i2c_bus=1, address=i2c_addr, frequency=freq, simulate=False)

    try:
        # Go to center
        logger.info(f"Moving to center ({center}μs)")
        pwm.set_pulse_width(ch, center)
        time.sleep(args.hold)

        # Sweep to min
        logger.info(f"Sweeping to min ({min_pulse}μs)")
        sweep(pwm, ch, center, min_pulse, args.step, args.delay)
        time.sleep(args.hold)

        # Sweep back to center
        logger.info(f"Sweeping back to center ({center}μs)")
        sweep(pwm, ch, min_pulse, center, args.step, args.delay)
        time.sleep(args.hold)

        # Sweep to max
        logger.info(f"Sweeping to max ({max_pulse}μs)")
        sweep(pwm, ch, center, max_pulse, args.step, args.delay)
        time.sleep(args.hold)

        # Sweep back to center
        logger.info(f"Sweeping back to center ({center}μs)")
        sweep(pwm, ch, max_pulse, center, args.step, args.delay)
        time.sleep(args.hold)

        print("\n✅ Test complete!")
        return 0

    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        return 2

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    finally:
        try:
            # Disable channel
            pwm.set_pwm(ch, 0, 0)
        except Exception:
            pass
        pwm.close()


if __name__ == "__main__":
    raise SystemExit(main())