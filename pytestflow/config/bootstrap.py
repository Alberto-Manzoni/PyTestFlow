from pytestflow.config.loader import load_user_config
from pytestflow.config.runtime import build_runtime_config


def get_config():
    user_config = load_user_config()
    return build_runtime_config(user_config)