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


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse the text of a .leitumenv file and return a dict of key/value pairs.

    Rules:
    - Blank lines and comment lines (first non-whitespace is ``#``) are skipped.
    - A leading ``export `` prefix (case-sensitive) is stripped.
    - The key and value are split on the first ``=`` only.
    - Surrounding single or double quotes are stripped from the value.
    - Lines without ``=`` are silently skipped.
    - No ``${VAR}`` expansion is performed inside the file.
    - Duplicate keys: last occurrence wins.
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :]
        if "=" not in stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        key = key.strip()
        if not key:
            continue
        value = raw_value
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result
