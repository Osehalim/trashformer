"""
Configuration loader for Trashformer robot.

Handles loading and parsing YAML configuration files with validation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """Load and manage configuration files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to configuration file (defaults to config/default.yaml)
        """
        if config_path is None:
            config_path = "config/default.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        if self.config_path.exists():
            self.load()
        else:
            logger.warning(f"Config file not found: {self.config_path}")
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dict containing configuration
        """
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return self.config
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'arm.servo_pins' or 'camera.width')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            config.get('arm.servo_pins')
            config.get('camera.fps', 30)
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            if default is not None:
                logger.debug(f"Config key '{key}' not found, using default: {default}")
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name (e.g., 'arm', 'camera', 'drive')
            
        Returns:
            Dictionary containing section configuration
        """
        return self.config.get(section, {})
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        logger.debug(f"Set config '{key}' = {value}")
    
    def save(self, path: Optional[str] = None):
        """
        Save current configuration to YAML file.
        
        Args:
            path: Optional path to save to (defaults to original path)
        """
        save_path = Path(path) if path else self.config_path
        
        try:
            with open(save_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info(f"Saved configuration to {save_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def __repr__(self):
        """String representation of configuration."""
        return f"ConfigLoader(path={self.config_path}, keys={list(self.config.keys())})"


# Global config instance (singleton pattern)
_global_config: Optional[ConfigLoader] = None


def load_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Load global configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigLoader instance
    """
    global _global_config
    _global_config = ConfigLoader(config_path)
    return _global_config


def get_config() -> ConfigLoader:
    """
    Get the global configuration instance.
    
    Returns:
        ConfigLoader instance
        
    Raises:
        RuntimeError: If config hasn't been loaded yet
    """
    if _global_config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _global_config


if __name__ == "__main__":
    # Test the config loader
    from utils.logger import setup_logging
    setup_logging()
    
    # Try to load default config
    try:
        config = load_config("config/default.yaml")
        print(f"Loaded config: {config}")
        print(f"Robot name: {config.get('robot.name', 'Unknown')}")
        print(f"Arm servos: {config.get('arm.servo_pins', [])}")
    except Exception as e:
        print(f"Could not load config: {e}")
        print("This is expected if config/default.yaml doesn't exist yet")