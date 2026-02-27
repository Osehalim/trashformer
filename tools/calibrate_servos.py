#!/usr/bin/env python3
"""
tools/calibrate_servos.py — Interactive PCA9685 servo calibration (with parking)

What it does:
- Loads config/default.yaml via ConfigLoader (dot-notation keys)
- Initializes PCA9685
- Lets you calibrate ONE servo at a time by jogging pulse width (μs)
- Lets you "park" other servos at fixed pulse widths while calibrating (e.g., shoulder up)
- Saves results to data/calibration/servo_limits.json

Safety:
- Lift arm / keep clear of collisions.
- Use external 5–6V servo power supply.
- Common ground between servo supply and Pi.
- Go slow near mechanical limits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from utils.config_loader import load_config, ConfigLoader
from utils.logger import setup_logging, get_logger
from arm.pca9685_driver import PCA9685

logger = get_logger(__name__)

CALIB_PATH = Path("data/calibration/servo_limits.json")
CALIB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Reasonable hard clamps to avoid accidental crazy pulses
PULSE_LO = 400
PULSE_HI = 2600


def load_existing_calibration() -> Dict:
    if CALIB_PATH.exists():
        try:
            return json.loads(CALIB_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_calibration(data: Dict) -> None:
    CALIB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def choose_servo(servo_channels: Dict[str, int]) -> Tuple[str, int]:
    names = list(servo_channels.keys())
    print("\nAvailable servos:")
    for i, n in enumerate(names):
        print(f"  {i}: {n} (channel {servo_channels[n]})")

    idx = int(input("\nSelect TARGET servo index: ").strip())
    name = names[idx]
    return name, int(servo_channels[name])


def ask_int(prompt: str, default: Optional[int] = None) -> Optional[int]:
    s = input(prompt).strip()
    if not s:
        return default
    try:
        return int(s)
    except ValueError:
        return default


def setup_parking(servo_channels: Dict[str, int], target_name: str) -> Dict[str, int]:
    """
    Return mapping of servo_name -> parked_pulse_us.
    """
    parked: Dict[str, int] = {}
    names = [n for n in servo_channels.keys() if n != target_name]

    if not names:
        return parked

    print("\nParking (optional):")
    print("You can park other servos at a fixed pulse while calibrating the target.")
    print("Example: park shoulder at ~1600–1900us so elbow can rotate freely.\n")

    # Ask how many to park (0..2 is usually enough)
    count = ask_int("How many servos do you want to park? (0/1/2) [0]: ", default=0)
    if count is None:
        count = 0
    count = max(0, min(2, count))

    for k in range(count):
        print("\nParkable servos:")
        for i, n in enumerate(names):
            print(f"  {i}: {n} (channel {servo_channels[n]})")

        idx = ask_int(f"Select servo #{k+1} to park [skip]: ", default=None)
        if idx is None:
            break
        if idx < 0 or idx >= len(names):
            print("Invalid selection, skipping.")
            continue

        park_name = names[idx]
        park_pulse = ask_int(f"Enter pulse to HOLD for '{park_name}' in us (e.g., 1700): ", default=None)
        if park_pulse is None:
            print("No pulse entered, skipping this parked servo.")
            continue

        park_pulse = max(PULSE_LO, min(PULSE_HI, park_pulse))
        parked[park_name] = park_pulse
        print(f"Will park {park_name} at {park_pulse}us")

    return parked


def apply_parking(pwm: PCA9685, servo_channels: Dict[str, int], parked: Dict[str, int]) -> None:
    for name, pulse in parked.items():
        ch = int(servo_channels[name])
        pwm.set_pulse_width(ch, int(pulse))


def interactive_calibration(
    pwm: PCA9685,
    servo_channels: Dict[str, int],
    target_name: str,
    target_channel: int,
    parked: Dict[str, int],
) -> Dict:
    # Start near center; you can adjust
    pulse = 1500
    step_small = 10
    step_big = 50

    min_pulse: Optional[int] = None
    max_pulse: Optional[int] = None
    center_pulse: Optional[int] = None

    print("\nControls:")
    print("  a/d  = -/+ 10us")
    print("  A/D  = -/+ 50us")
    print("  z/x  = -/+ 1us  (fine)")
    print("  c    = save CENTER pulse (use for 'forward' reference if needed)")
    print("  s    = save MIN safe pulse")
    print("  e    = save MAX safe pulse")
    print("  p    = re-apply parking pulses (if something moved)")
    print("  q    = quit and save")
    print()

    while True:
        # Keep parked servos held while you work
        apply_parking(pwm, servo_channels, parked)

        # Drive target
        pulse = max(PULSE_LO, min(PULSE_HI, pulse))
        pwm.set_pulse_width(target_channel, pulse)

        cmd = input(f"[TARGET={target_name}] pulse={pulse}us > ").strip()

        if cmd == "a":
            pulse -= step_small
        elif cmd == "d":
            pulse += step_small
        elif cmd == "A":
            pulse -= step_big
        elif cmd == "D":
            pulse += step_big
        elif cmd == "z":
            pulse -= 1
        elif cmd == "x":
            pulse += 1
        elif cmd == "c":
            center_pulse = pulse
            print(f"Saved CENTER pulse = {center_pulse}")
        elif cmd == "s":
            min_pulse = pulse
            print(f"Saved MIN pulse = {min_pulse}")
        elif cmd == "e":
            max_pulse = pulse
            print(f"Saved MAX pulse = {max_pulse}")
        elif cmd == "p":
            apply_parking(pwm, servo_channels, parked)
            print("Re-applied parking pulses.")
        elif cmd == "q":
            break

    return {
        "min_pulse": min_pulse,
        "max_pulse": max_pulse,
        "center_pulse": center_pulse,  # useful for elbow-forward reference
        "invert": False,
        "offset_deg": 0.0,
        "notes": {
            "parked": parked
        }
    }


def main() -> int:
    setup_logging()

    cfg: ConfigLoader = load_config("config/default.yaml")

    i2c_bus = int(cfg.get("hardware.i2c_bus", 1))
    i2c_address = int(cfg.get("hardware.i2c_address", 0x40))
    pwm_freq = int(cfg.get("arm.pwm_frequency", 50))

    servo_channels = cfg.get("arm.servo_channels", {})
    if not isinstance(servo_channels, dict) or not servo_channels:
        print("ERROR: Missing arm.servo_channels in config/default.yaml")
        return 1

    pwm = PCA9685(i2c_bus=i2c_bus, address=i2c_address, frequency=pwm_freq, simulate=False)

    try:
        target_name, target_channel = choose_servo(servo_channels)
        parked = setup_parking(servo_channels, target_name)

        print("\nParking summary:")
        if parked:
            for n, p in parked.items():
                print(f"  - {n}: {p}us")
        else:
            print("  (none)")

        result = interactive_calibration(pwm, servo_channels, target_name, target_channel, parked)

        data = load_existing_calibration()
        data[target_name] = result
        save_calibration(data)

        print(f"\n✅ Calibration saved to: {CALIB_PATH}")
        print("Tip: calibrate shoulder first, then park shoulder up while calibrating elbow.")
        return 0

    finally:
        # Stop outputs safely
        try:
            for name, ch in servo_channels.items():
                pwm.set_pwm(int(ch), 0, 0)
        except Exception:
            pass
        pwm.close()


if __name__ == "__main__":
    raise SystemExit(main())