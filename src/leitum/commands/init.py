"""leitum init command."""

from leitum.config.io import write_empty_state, write_example_providers_config
from leitum.config.paths import ensure_dirs, providers_config_path, state_path


def run_init(force: bool = False, yes: bool = False) -> None:
    ensure_dirs()

    cfg_path = providers_config_path()
    if cfg_path.exists() and not force:
        print(f"Config already exists at {cfg_path}. Use --force to overwrite.")
    elif cfg_path.exists() and force:
        if not yes:
            answer = input(f"Overwrite {cfg_path}? [y/N] ").strip().lower()
            if answer != "y":
                print("Aborted.")
                raise SystemExit(0)
        write_example_providers_config(cfg_path)
        print(f"Created {cfg_path}")
    else:
        write_example_providers_config(cfg_path)
        print(f"Created {cfg_path}")

    st_path = state_path()
    if not st_path.exists():
        write_empty_state(st_path)
        print(f"Created {st_path}")

    print("\nSet REQUESTY_API_KEY in your shell and run `leitum claude` to start.")
