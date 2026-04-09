import argparse
import os
import shutil
import sys
from pathlib import Path
from importlib import resources

APP_DIR_NAME = "pytestflow"

# --------------------
# Template map
# --------------------
TEMPLATE_SOURCE_MAP = {
    "process_models": ("pytestflow", "bootstrap_templates/process_models"),
    "test_sequences": ("pytestflow", "bootstrap_templates/test_sequences"),
    "custom_step_types": ("pytestflow", "bootstrap_templates/custom_step_types"),
}

# --------------------
# Workspace helpers
# --------------------
def resolve_workspace_root(custom_path: str | None = None) -> Path:
    if custom_path:
        return Path(custom_path).expanduser().resolve()

    home = Path.home()
    if sys.platform.startswith("win"):
        base = Path(os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or (home / "AppData/Local"))
    elif sys.platform == "darwin":
        base = home / "Library/Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or (home / ".local/share"))

    return (base / APP_DIR_NAME).resolve()


def workspace_paths(root: Path) -> dict[str, Path]:
    subdirs = ["process_models", "test_sequences", "test_reports", "custom_step_types"]
    paths = {"root": root}
    for name in subdirs:
        paths[name] = root / name
    return paths

# --------------------
# Copy helper robusto
# --------------------
def copy_resource_tree(package: str, src_path: str, dest: Path):
    """
    Copia ricorsivamente file e cartelle dal package Python a dest.
    Funziona anche su pacchetti installati da GitHub o zip.
    """
    dest.mkdir(parents=True, exist_ok=True)

    # Scansione sicura dei contenuti
    for item in resources.contents(package):
        if not item.startswith(Path(src_path).name):
            continue

        relative = Path(item).relative_to(Path(src_path).name)
        target = dest / relative

        try:
            if resources.is_resource(package, item):
                # file
                with resources.as_file(resources.files(package).joinpath(item)) as f:
                    shutil.copy2(f, target)
            else:
                # directory
                copy_resource_tree(package, item, target)
        except Exception:
            # ignora file non compatibili
            pass

# --------------------
# Copy templates
# --------------------
def _copy_templates(paths: dict[str, Path]) -> list[tuple[str, Path]]:
    copied = []

    for key, (pkg, folder) in TEMPLATE_SOURCE_MAP.items():
        try:
            dest = paths[key]
            copy_resource_tree(pkg, folder, dest)
            copied.append((key, dest))
        except Exception as e:
            print(f"[ERROR] Cannot copy templates for {key}: {e}")

    # Copia config.yaml
    try:
        config_dest = paths["root"] / "config.yaml"
        if not config_dest.exists():
            with resources.as_file(resources.files("pytestflow").joinpath("bootstrap_templates/config.yaml")) as f:
                shutil.copy2(f, config_dest)
            copied.append(("config", config_dest))
        else:
            print(f"[skipped] config.yaml already exists at {config_dest}")
    except Exception as e:
        print(f"[ERROR] Could not copy default config.yaml: {e}")

    return copied

# --------------------
# Initialize workspace
# --------------------
def initialize_workspace_interactive() -> dict[str, Path]:
    print("PyTestFlow workspace initialization:")
    choice = input(
        "Install templates in current folder (c) or default location (d)? [d/c]: "
    ).strip().lower()

    if choice == "c":
        root = Path.cwd()
    else:
        root = resolve_workspace_root()

    paths = workspace_paths(root)
    root.mkdir(parents=True, exist_ok=True)
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    copied = _copy_templates(paths)

    print(f"\nPyTestFlow workspace initialized at: {root}")
    if copied:
        for key, target in copied:
            print(f"[copied] {key}: {target}")
    else:
        print("[copied] No new files copied, templates already exist.")

    # Set environment variable prompt
    if sys.platform.startswith("win"):
        print(f"\nSet environment variable for this session in PowerShell:\n$env:PYTESTFLOW_HOME='{root}'")
    else:
        print(f"\nSet environment variable for this session in bash/zsh:\nexport PYTESTFLOW_HOME='{root}'")

    return paths

# --------------------
# CLI
# --------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pytestflow",
        description="PyTestFlow CLI: initialize workspace or start backend",
    )
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser(
        "start",
        help="Start backend and serve the GUI",
    )
    start_parser.add_argument(
        "--open",
        action="store_true",
        help="Open the GUI URL in your default browser",
    )

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize PyTestFlow workspace and copy templates",
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "start"

    if command == "init":
        initialize_workspace_interactive()
        return 0

    if command == "start":
        from pytestflow.backend.start_backend import main as start_backend
        start_backend(open_browser=getattr(args, "open", False))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())