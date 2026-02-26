#!/usr/bin/env python3
"""
Simple single-servo test using Raspberry Pi GPIO (no PCA9685)

- Uses pigpio for stable hardware PWM
- Moves servo gently around center position
- Returns to safe position before exiting

Wiring:
Signal  -> GPIO18 (pin 12)
Ground  -> Pi GND (shared with servo supply)
Power   -> External 5-6V supply (NOT Pi 5V)
"""

import pigpio
import time
import sys

GPIO_PIN = 18            # Hardware PWM pin
PWM_FREQUENCY = 50       # Standard servo frequency (50 Hz)

SAFE_PULSE = 1500        # ~90 degrees
MIN_PULSE = 1000         # ~0 degrees (adjust if needed)
MAX_PULSE = 2000         # ~180 degrees (adjust if needed)

STEP_DELAY = 0.8         # Time between moves


def main():
    print("\n=== Single Servo Test (Direct Pi PWM) ===")
    print("Make sure servo is powered externally and robot is clear.\n")

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: pigpio daemon not running.")
        print("Run: sudo systemctl start pigpiod")
        return 1

    try:
        # Set frequency
        pi.set_PWM_frequency(GPIO_PIN, PWM_FREQUENCY)

        def move(pulse):
            pulse = max(500, min(2500, pulse))
            pi.set_servo_pulsewidth(GPIO_PIN, pulse)
            print(f"  Pulse: {pulse} µs")
            time.sleep(STEP_DELAY)

        # Start at safe center
        move(SAFE_PULSE)

        # Small movement test
        move(SAFE_PULSE - 200)
        move(SAFE_PULSE)
        move(SAFE_PULSE + 200)
        move(SAFE_PULSE)

        print("\n✅ Servo test complete.")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        # Stop signal
        pi.set_servo_pulsewidth(GPIO_PIN, 0)
        pi.stop()
        print("Servo signal stopped safely.")

    return 0


if __name__ == "__main__":
    sys.exit(main())