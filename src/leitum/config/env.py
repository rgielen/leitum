import os
import re

_INTERPOLATION_RE = re.compile(r"\$\{([^}]+)\}")


def interpolate(value: str, environ: dict[str, str] | None = None) -> str:
    """Resolve ${VAR} and ${VAR:-default} references in value."""
    env = environ if environ is not None else dict(os.environ)

    def replace(match: re.Match[str]) -> str:
        expr = match.group(1)
        if ":-" in expr:
            var_name, default = expr.split(":-", 1)
            return env.get(var_name.strip(), default)
        else:
            var_name = expr.strip()
            if var_name not in env:
                raise ValueError(f"Required env var `{var_name}` not set")
            return env[var_name]

    return _INTERPOLATION_RE.sub(replace, value)


def interpolate_dict(d: dict[str, str], environ: dict[str, str] | None = None) -> dict[str, str]:
    return {k: interpolate(v, environ) for k, v in d.items()}
