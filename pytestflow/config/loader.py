# esempio loader combinato
from pytestflow.config.runtime import build_runtime_config
import yaml
from pathlib import Path
import os

def load_user_config():
    root = Path(os.getenv("PYTESTFLOW_HOME") or Path.cwd())
    config_path = root / "config.yaml"

    if not config_path.exists():
        from pytestflow.config.runtime import save_default_config
        save_default_config(config_path)
        print(f"[dev] Config.yaml creato in {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


# uso finale
user_config = load_user_config()
config = build_runtime_config(user_config)
print(config["process_models"])  # Path assoluto pronto da usare