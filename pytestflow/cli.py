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
    "process_models": ("bootstrap_templates", "process_models"),
    "test_sequences": ("bootstrap_templates", "test_sequences"),
    "custom_step_types": ("bootstrap_templates", "custom_step_types"),
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


def _copy_templates(paths: dict[str, Path]) -> list[tuple[str, Path]]:
    copied = []

    for key, inner_path in TEMPLATE_SOURCE_MAP.items():
        destination_dir = paths[key]
        try:
            # riferimento corretto al pacchetto pytestflow
            source_dir = resources.files("pytestflow").joinpath(*inner_path)

            with resources.as_file(source_dir) as source_path:
                source_dir_path = Path(source_path)
        except Exception as e:
            print(f"[ERROR] Cannot load templates for {key}: {e}")
            continue

        for src in source_dir_path.rglob("*"):
            if src.is_file():
                relative = src.relative_to(source_dir_path)
                target = destination_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                print(f"[copied] {target}")
                copied.append((key, target))

    # Copia config.yaml
    try:
        config_dest = paths["root"] / "config.yaml"
        if not config_dest.exists():
            source_file = resources.files("pytestflow").joinpath("bootstrap_templates", "config.yaml")
            with resources.as_file(source_file) as f:
                shutil.copy2(f, config_dest)
                print(f"[copied] config.yaml -> {config_dest}")
                copied.append(("config", config_dest))
        else:
            print(f"[skipped] config.yaml already exists at {config_dest}")
    except Exception as e:
        print(f"[ERROR] Could not copy default config.yaml: {e}")

    return copied


def initialize_workspace_interactive() -> dict[str, Path]:
    print("PyTestFlow workspace initialization:")
    choice = input("Install templates in current folder (c) or default location (d)? [d/c]: ").strip().lower()

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

    subparsers.add_parser(
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