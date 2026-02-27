"""
Configuration loader for Trashformer robot.

Loads YAML configuration and supports:
- dot-notation access (e.g., 'arm.pwm_frequency')
- section access (e.g., get_section('arm'))
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = "config/default.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        if self.config_path.exists():
            self.load()
        else:
            logger.warning(f"Config file not found: {self.config_path}")

    def load(self) -> Dict[str, Any]:
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("Config YAML did not parse into a dictionary.")
            self.config = data
            logger.info(f"Loaded configuration from {self.config_path}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value: Any = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        sec = self.config.get(section, {})
        return sec if isinstance(sec, dict) else {}

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        cur = self.config

        for k in keys[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]

        cur[keys[-1]] = value

    def save(self, path: Optional[str] = None) -> None:
        save_path = Path(path) if path else self.config_path
        try:
            with save_path.open("w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info(f"Saved configuration to {save_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    def __repr__(self) -> str:
        return f"ConfigLoader(path={self.config_path}, keys={list(self.config.keys())})"


_global_config: Optional[ConfigLoader] = None


def load_config(config_path: Optional[str] = None) -> ConfigLoader:
    global _global_config
    _global_config = ConfigLoader(config_path)
    return _global_config


def get_config() -> ConfigLoader:
    if _global_config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _global_config