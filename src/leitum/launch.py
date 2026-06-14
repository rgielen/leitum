"""Build sub-environment and exec claude."""

import os
import shutil
import sys

from leitum.config.env import interpolate, interpolate_dict
from leitum.config.models import Provider
from leitum.selection.resolver import ResolvedModels

_LEITUM_VARS = frozenset(
    {
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    }
)


def build_env(
    *,
    provider: Provider,
    models: ResolvedModels,
    project_extra_env: dict[str, str],
    base_environ: dict[str, str] | None = None,
    verbose: bool = False,
) -> dict[str, str]:
    env = dict(base_environ if base_environ is not None else os.environ)

    auth_var = provider.auth.env_var
    token = interpolate(provider.auth.token)

    # Remove ANTHROPIC_API_KEY if we're using a different env var
    if auth_var != "ANTHROPIC_API_KEY":
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
            if verbose:
                print("  Removed ANTHROPIC_API_KEY from environment", file=sys.stderr)

    env["ANTHROPIC_BASE_URL"] = provider.base_url
    env[auth_var] = token

    if verbose:
        print(f"  Set ANTHROPIC_BASE_URL={provider.base_url}", file=sys.stderr)
        print(f"  Set {auth_var}=***redacted***", file=sys.stderr)

    slot_vars = {
        "opus": "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "sonnet": "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "haiku": "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    }
    for slot, var in slot_vars.items():
        val = models.get(slot)  # type: ignore[arg-type]
        if val:
            env[var] = val
            if verbose:
                print(f"  Set {var}={val}", file=sys.stderr)

    # provider.extra_env — warn on collision with leitum-managed vars
    try:
        prov_extra = interpolate_dict(provider.extra_env)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc

    for k, v in prov_extra.items():
        if k in _LEITUM_VARS:
            print(
                f"Warning: provider.extra_env key '{k}' conflicts"
                " with a leitum-managed variable; ignoring.",
                file=sys.stderr,
            )
        else:
            env[k] = v

    # project.extra_env — wins over provider.extra_env, but not leitum-managed vars
    try:
        proj_extra = interpolate_dict(project_extra_env)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc

    for k, v in proj_extra.items():
        if k in _LEITUM_VARS:
            print(
                f"Warning: project extra_env key '{k}' conflicts"
                " with a leitum-managed variable; ignoring.",
                file=sys.stderr,
            )
        else:
            if verbose and k in prov_extra:
                print(f"  {k} overridden by project extra_env", file=sys.stderr)
            env[k] = v

    return env


def build_argv(
    pass_through: list[str],
    models: ResolvedModels,
) -> list[str]:
    argv = ["claude", *pass_through]
    if models.start:
        has_model_flag = any(
            a == "--model" or a.startswith("--model=") or a == "-m" for a in pass_through
        )
        if not has_model_flag:
            argv.extend(["--model", models.start])
    return argv


def exec_claude(
    *,
    provider: Provider,
    models: ResolvedModels,
    pass_through: list[str],
    project_extra_env: dict[str, str],
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    claude_path = shutil.which("claude")
    if claude_path is None:
        print(
            "Error: 'claude' binary not found in PATH.\n"
            "Install Claude Code: https://docs.claude.com/en/docs/claude-code/quickstart",
            file=sys.stderr,
        )
        raise SystemExit(5)

    if verbose:
        print(f"Provider: {provider.name} ({provider.base_url})", file=sys.stderr)
        print("Environment changes:", file=sys.stderr)

    env = build_env(
        provider=provider,
        models=models,
        project_extra_env=project_extra_env,
        verbose=verbose,
    )
    argv = build_argv(pass_through, models)

    if dry_run:
        print("# leitum --dry-run: resolved environment (leitum-set variables only)")
        auth_var = provider.auth.env_var
        leitum_keys = [
            "ANTHROPIC_BASE_URL",
            auth_var,
            "ANTHROPIC_DEFAULT_OPUS_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        ]
        for k in leitum_keys:
            if k in env:
                val = "***redacted***" if k == auth_var else env[k]
                print(f"  {k}={val}")
        print(f"\n# exec: {' '.join(argv)}")
        return

    if verbose:
        print(f"Exec: {' '.join(argv)}", file=sys.stderr)

    os.execvpe("claude", argv, env)
