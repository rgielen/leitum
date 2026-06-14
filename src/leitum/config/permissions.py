import stat
import sys
from pathlib import Path


def check_file_permissions(path: Path) -> bool:
    """Return True if permissions are 0600 or stricter. Warn otherwise."""
    if not path.exists():
        return True
    resolved = path.resolve()
    mode = resolved.stat().st_mode
    world_or_group_readable = bool(
        mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
    )
    if world_or_group_readable:
        print(
            f"Warning: {path} has permissions {oct(stat.S_IMODE(mode))}."
            f" Recommended: chmod 600 {path}",
            file=sys.stderr,
        )
        return False
    return True


def create_with_mode(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)
