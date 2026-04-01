from typing import Iterator, Tuple, Union
from pytestflow.core.core import StepWrapper
from pytestflow.core.sequence import TestSequence
import inspect
import uuid
import os

PTF_NAMESPACE = uuid.UUID("9c0cb974-3f6e-40ff-b4ea-a30f68fe35b7")

def walk_sequence(
    sequence: "TestSequence",
    base_path: Tuple[str, ...] = (),
) -> Iterator[Tuple[Union["TestSequence", "StepWrapper"], Tuple[str, ...]]]:
    """
    Itera ricorsivamente su una TestSequence e sui suoi step,
    restituendo (nodo, path) per calcolare UUID coerenti.
    """

    # path per la sequence stessa
    seq_path = (*base_path, f"SEQ:{sequence.name}")
    yield sequence, seq_path

    # funzione interna per processare liste di step
    def walk_steps(step_list, section_name):
        for idx, step in enumerate(step_list):
            step_path = (*seq_path, f"{section_name}[{idx}]")
            if isinstance(step, TestSequence):
                # ricorsione
                yield from walk_sequence(step, step_path)
            else:
                # passo normale / Prefect step
                yield step, (*step_path, f"STEP:{getattr(step, 'name', 'unnamed')}")
    
    walk_lists = [
        ("SETUP", getattr(sequence, "setup_steps", [])),
        ("MAIN", getattr(sequence, "main_steps", [])),
        ("CLEANUP", getattr(sequence, "cleanup_steps", [])),
    ]

    for section_name, steps in walk_lists:
        yield from walk_steps(steps, section_name)


def get_root_sequence_uuid(entrypoint_fn: callable) -> uuid.UUID:
    """
    Calcola un UUID stabile per la root TestSequence basandosi sulla funzione entrypoint.
    - entrypoint_fn: la funzione che crea la root TestSequence (ENTRYPOINT)
    """
    real_fn = inspect.unwrap(entrypoint_fn)

    try:
        file_path = os.path.realpath(inspect.getfile(real_fn))
    except Exception:
        file_path = "nofile"

    key = f"RootSequence:{file_path}:{real_fn.__qualname__}"
    return uuid.uuid5(PTF_NAMESPACE, key)

def resolve_uuids(root_sequence: "TestSequence", entrypoint_fn: callable):
    root_id = get_root_sequence_uuid(entrypoint_fn)

    for node, path in walk_sequence(root_sequence, (str(root_id),)):
        node.static_uuid = uuid.uuid5(
            PTF_NAMESPACE,
            "/".join(path)
        )

