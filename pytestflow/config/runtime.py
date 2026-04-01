# pytestflow/config/runtime.py
from pathlib import Path
import os
import yaml

DEFAULT_FOLDERS = {
    "examples": "examples",
    "process_models": "process_models",
    "test_sequences": "test_sequences",
    "test_reports": "test_reports",
    "custom_step_types": "custom_step_types",
}

DEFAULT_CONFIG = {
    "http_host": "127.0.0.1",
    "http_port": 8000,
    "ws_host": "127.0.0.1",
    "ws_port": 8765,
    "zmq_host": "127.0.0.1",
    "zmq_port": 5555,
    **DEFAULT_FOLDERS,
}


def build_runtime_config(user_config: dict) -> dict:
    """
    Converte i path relativi del YAML in Path assoluti basati su PYTESTFLOW_HOME
    Applica valori di default se mancano
    """
    root = Path(os.getenv("PYTESTFLOW_HOME") or Path.cwd()).resolve()
    runtime_config = DEFAULT_CONFIG.copy()

    # sovrascrive default con valori presenti nel YAML
    runtime_config.update(user_config or {})

    # trasforma tutte le cartelle relative → assolute
    for key in DEFAULT_FOLDERS.keys():
        runtime_config[key] = (root / runtime_config[key]).resolve()

    # aggiunge root come riferimento
    runtime_config["root"] = root

    return runtime_config


def save_default_config(path: Path | str):
    """Salva un config.yaml di default nella path indicata"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(DEFAULT_CONFIG, f)