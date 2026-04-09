import argparse
import sys
from pathlib import Path
import shutil
from importlib import resources

APP_DIR_NAME = "pytestflow"

# Template map
TEMPLATE_SOURCE_MAP = {
    "process_models": "process_models",
    "test_sequences": "test_sequences",
    "custom_step_types": "custom_step_types",
}

def resolve_workspace_root(custom_path: str | None = None) -> Path:
    if custom_path:
        return Path(custom_path).expanduser().resolve()

    home = Path.home()
    if sys.platform.startswith("win"):
        base = Path(sys.getenv("LOCALAPPDATA") or sys.getenv("APPDATA") or (home / "AppData/Local"))
    elif sys.platform == "darwin":
        base = home / "Library/Application Support"
    else:
        base = Path(sys.getenv("XDG_DATA_HOME") or (home / ".local/share"))
    return (base / APP_DIR_NAME).resolve()

def workspace_paths(root: Path) -> dict[str, Path]:
    subdirs = ["process_models", "test_sequences", "test_reports", "custom_step_types"]
    paths = {"root": root}
    for name in subdirs:
        paths[name] = root / name
    return paths

def copy_package_folder(package: str, folder: str, dest: Path) -> None:
    """Copia tutti i file e sottocartelle di una cartella del package in dest"""
    try:
        root = resources.files(package).joinpath("bootstrap_templates", folder)
    except Exception as e:
        print(f"[ERROR] Cannot access {folder} in {package}: {e}")
        return

    def recurse(source, target):
        for item in source.iterdir():
            if item.is_file():
                target_path = target / item.name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with resources.as_file(item) as f:
                    shutil.copy2(f, target_path)
                print(f"[copied] {target_path}")
            elif item.is_dir():
                recurse(item, target / item.name)

    recurse(root, dest)

def initialize_workspace_interactive() -> dict[str, Path]:
    print("PyTestFlow workspace initialization:")
    choice = input("Install templates in current folder (c) or default location (d)? [d/c]: ").strip().lower()
    root = Path.cwd() if choice == "c" else resolve_workspace_root()
    
    paths = workspace_paths(root)
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    # Copia template
    for key, folder in TEMPLATE_SOURCE_MAP.items():
        copy_package_folder("pytestflow", folder, paths[key])

    # Copia config.yaml
    try:
        config_dest = paths["root"] / "config.yaml"
        if not config_dest.exists():
            with resources.as_file(resources.files("pytestflow").joinpath("bootstrap_templates", "config.yaml")) as f:
                shutil.copy2(f, config_dest)
            print(f"[copied] config.yaml -> {config_dest}")
        else:
            print(f"[skipped] config.yaml already exists at {config_dest}")
    except Exception as e:
        print(f"[ERROR] Could not copy default config.yaml: {e}")

    print(f"\nPyTestFlow workspace initialized at: {root}")

    if sys.platform.startswith("win"):
        print(f"\nSet environment variable for this session in PowerShell:\n$env:PYTESTFLOW_HOME='{root}'")
    else:
        print(f"\nSet environment variable for this session in bash/zsh:\nexport PYTESTFLOW_HOME='{root}'")

    return paths

# --------------------
# CLI
# --------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pytestflow", description="PyTestFlow CLI")
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start backend and serve the GUI")
    start_parser.add_argument("--open", action="store_true", help="Open the GUI URL in your browser")

    subparsers.add_parser("init", help="Initialize workspace and copy templates")
    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        initialize_workspace_interactive()
        return 0
    elif args.command == "start":
        from pytestflow.backend.start_backend import main as start_backend
        start_backend(open_browser=getattr(args, "open", False))
        return 0
    parser.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())