import os
from pathlib import Path
import yaml


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._config = None
        return cls._instance

    def get_config(self, reload=False):
        if self._config is None or reload:
            self._config = self._load_config()
        return self._config

    def _load_config(self):
        home = os.getenv("PYTESTFLOW_HOME")

        if not home:
            raise Exception(
                "PYTESTFLOW_HOME not set. Run 'pytestflow init' first."
            )

        root = Path(home)
        config_path = root / "config.yaml"

        if not config_path.exists():
            raise Exception("Configuration file not found.")

        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def get_path(self, key):
        config = self.get_config()

        if key not in config:
            raise KeyError(f"Missing config key: {key}")

        home = Path(os.getenv("PYTESTFLOW_HOME"))
        return home / config[key]