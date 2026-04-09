import importlib.util
import sys
from pathlib import Path
from prefect import flow
from prefect.context import get_run_context
from pytestflow.config.config_manager import ConfigManager

config = ConfigManager()
process_models_dir = config.get_path("process_models")

def load_sequential_model(process_models_dir: str):
    file_path = Path(process_models_dir) / "sequential_model.py"

    spec = importlib.util.spec_from_file_location(
        "user_sequential_model",
        file_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["user_sequential_model"] = module
    spec.loader.exec_module(module)

    return module.SequentialProcessModel


@flow()
def run_sequence_file(process_model_callbacks):
    # Following line are because we cannot do @flow(name=test_sequence.name)
    ctx = get_run_context()

    ctx.flow_run.name = process_model_callbacks["main_sequence"].name

    my_proc_model = load_sequential_model(process_models_dir)

    process_model = my_proc_model(
        name=process_model_callbacks["main_sequence"].name,
        callbacks=process_model_callbacks
    )
    return process_model.run(return_state=True)
