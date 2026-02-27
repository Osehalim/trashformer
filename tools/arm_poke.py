#!/usr/bin/env python3
"""
tools/arm_poke.py — Interactive arm poke test (angles)

Keys:
  1/2/3 select shoulder/elbow/gripper
  a/d decrease/increase angle by step
  o open gripper, c close gripper
  h home, n neutral, q quit

This uses ArmController (so it respects angle limits + calibration if loaded).
"""

from __future__ import annotations

from utils.logger import setup_logging, get_logger
from utils.config_loader import load_config
from arm.arm_controller import ArmController

logger = get_logger(__name__)


def main() -> int:
    setup_logging()
    cfg = load_config("config/default.yaml")

    joint = "shoulder"
    step = 5.0

    with ArmController(config=cfg, simulate=False) as arm:
        logger.info("Arm poke test started.")
        arm.home(speed=60, blocking=True)

        angles = arm.get_current_angles()
        cur = angles.get(joint) or 0.0

        while True:
            angles = arm.get_current_angles()
            cur = angles.get(joint) if angles.get(joint) is not None else cur
            print(f"\nSelected joint: {joint} | current: {cur}")
            print("Commands: 1/2/3 joint | a/d move | o open | c close | h home | n neutral | q quit")
            cmd = input("> ").strip().lower()

            if cmd == "q":
                break
            if cmd == "1":
                joint = "shoulder"
                continue
            if cmd == "2":
                joint = "elbow"
                continue
            if cmd == "3":
                joint = "gripper"
                continue

            if cmd == "h":
                arm.home(speed=70, blocking=True)
                continue
            if cmd == "n":
                arm.neutral(speed=70, blocking=True)
                continue

            if cmd == "o":
                arm.open_gripper(speed=80)
                continue
            if cmd == "c":
                arm.close_gripper(speed=80)
                continue

            if cmd == "a":
                target = (cur or 0.0) - step
                arm.move_to_angles({joint: target}, speed=60, blocking=True)
                continue
            if cmd == "d":
                target = (cur or 0.0) + step
                arm.move_to_angles({joint: target}, speed=60, blocking=True)
                continue

        logger.info("Exiting arm poke test.")
        arm.home(speed=60, blocking=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())