#!/usr/bin/env python3
"""
arm/calibration.py

Loads servo calibration saved by tools/calibrate_servos.py.

Expected file: data/calibration/servo_limits.json

Example structure:
{
  "shoulder": {"min_pulse": 520, "max_pulse": 2410, "center_pulse": 1500, ...},
  "elbow": {"min_pulse": 600, "max_pulse": 2100, "center_pulse": 1500, ...},
  "gripper": {"min_pulse": 500, "max_pulse": 2500, ...}
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

DEFAULT_CALIB_PATH = Path("data/calibration/servo_limits.json")


def load_servo_calibration(path: Path = DEFAULT_CALIB_PATH) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # ensure nested dicts
            cleaned = {}
            for k, v in data.items():
                if isinstance(v, dict):
                    cleaned[k] = v
            return cleaned
        return {}
    except Exception:
        return {}