"""Root typer application and subcommand registration."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(
    name="leitum",
    help="Launch Claude Code against alternative LLM routers.",
    add_completion=False,
    no_args_is_help=True,
)

provider_app = typer.Typer(help="Manage configured providers.", no_args_is_help=True)
app.add_typer(provider_app, name="provider")


# Shared state passed via typer Context
class _Opts:
    provider: str | None = None
    use_last_provider: bool = False
    model: str | None = None
    use_last_model: bool = False
    opus: str | None = None
    use_last_opus: bool = False
    sonnet: str | None = None
    use_last_sonnet: bool = False
    haiku: str | None = None
    use_last_haiku: bool = False
    refresh: bool = False
    no_project_config: bool = False
    project_config: Path | None = None
    dry_run: bool = False
    verbose: bool = False


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    provider: str | None = typer.Option(None, "--provider", "-p", help="Set provider."),
    use_last_provider: bool = typer.Option(
        False, "--use-last-provider", "-P", help="Reuse last provider."
    ),
    model: str | None = typer.Option(None, "--model", "-m", help="Set START model."),
    use_last_model: bool = typer.Option(
        False, "--use-last-model", "-M", help="Reuse last START model."
    ),
    opus: str | None = typer.Option(None, "--opus", "-o", help="Set OPUS model."),
    use_last_opus: bool = typer.Option(
        False, "--use-last-opus", "-O", help="Reuse last OPUS model."
    ),
    sonnet: str | None = typer.Option(None, "--sonnet", "-s", help="Set SONNET model."),
    use_last_sonnet: bool = typer.Option(
        False, "--use-last-sonnet", "-S", help="Reuse last SONNET model."
    ),
    haiku: str | None = typer.Option(None, "--haiku", "-k", help="Set HAIKU model."),
    use_last_haiku: bool = typer.Option(
        False, "--use-last-haiku", "-K", help="Reuse last HAIKU model."
    ),
    refresh: bool = typer.Option(
        False, "--refresh", "-r", help="Refresh model cache before selection."
    ),
    no_project_config: bool = typer.Option(
        False, "--no-project-config", help="Ignore leitum.yaml."
    ),
    project_config: Path | None = typer.Option(
        None, "--project-config", help="Use alternative project config."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print resolved env and exec line, do not launch."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging on stderr."),
    version: bool = typer.Option(False, "--version", help="Show version and exit.", is_eager=True),
) -> None:
    if version:
        import importlib.metadata

        ver = importlib.metadata.version("leitum")
        typer.echo(f"leitum {ver}")
        raise typer.Exit()

    ctx.ensure_object(_Opts)
    obj = ctx.obj
    obj.provider = provider
    obj.use_last_provider = use_last_provider
    obj.model = model
    obj.use_last_model = use_last_model
    obj.opus = opus
    obj.use_last_opus = use_last_opus
    obj.sonnet = sonnet
    obj.use_last_sonnet = use_last_sonnet
    obj.haiku = haiku
    obj.use_last_haiku = use_last_haiku
    obj.refresh = refresh
    obj.no_project_config = no_project_config
    obj.project_config = project_config
    obj.dry_run = dry_run
    obj.verbose = verbose

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help=(
        "Launch Claude Code via the configured provider.\n\n"
        "All arguments after 'claude' are passed through to the claude binary unchanged.\n"
        "See 'claude --help' for Claude Code's own options."
    ),
)
def claude(
    ctx: typer.Context,
    args: list[str] = typer.Argument(default=None),
) -> None:
    ctx.ensure_object(_Opts)
    opts: _Opts = ctx.obj
    pass_through = list(ctx.args) + (args or [])

    from leitum.commands.claude import run_claude

    run_claude(
        pass_through=pass_through,
        provider_flag=opts.provider,
        use_last_provider=opts.use_last_provider,
        model_flag=opts.model,
        use_last_model=opts.use_last_model,
        opus_flag=opts.opus,
        use_last_opus=opts.use_last_opus,
        sonnet_flag=opts.sonnet,
        use_last_sonnet=opts.use_last_sonnet,
        haiku_flag=opts.haiku,
        use_last_haiku=opts.use_last_haiku,
        refresh=opts.refresh,
        no_project_config=opts.no_project_config,
        project_config_path=opts.project_config,
        dry_run=opts.dry_run,
        verbose=opts.verbose,
    )


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing files."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts."),
) -> None:
    """Initialize leitum config directory and example providers file."""
    from leitum.commands.init import run_init

    run_init(force=force, yes=yes)


@app.command()
def refresh(
    ctx: typer.Context,
    provider_name: str | None = typer.Option(
        None, "--provider", "-p", help="Refresh specific provider only."
    ),
) -> None:
    """Delete model cache and re-fetch from providers."""
    from leitum.commands.refresh import run_refresh

    run_refresh(provider_name)


@app.command()
def doctor(
    project_config: Path | None = typer.Option(
        None, "--project-config", help="Path to project config."
    ),
) -> None:
    """Run sanity checks on config, permissions, and environment."""
    from leitum.commands.doctor import run_doctor

    run_doctor(project_config)


@app.command()
def completions(
    shell: str = typer.Argument(..., help="Shell: bash, zsh, or fish."),
) -> None:
    """Print shell completion script."""
    import subprocess

    if shell not in ("bash", "zsh", "fish"):
        typer.echo(f"Unsupported shell '{shell}'. Choose from: bash, zsh, fish.", err=True)
        raise typer.Exit(2)
    result = subprocess.run(
        ["leitum", "--show-completion", shell],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo(result.stdout, nl=False)
    else:
        typer.echo(result.stderr, err=True)
        raise typer.Exit(result.returncode)


@provider_app.command("list")
def provider_list() -> None:
    """List all configured providers."""
    from leitum.commands.provider import run_provider_list

    run_provider_list()


@provider_app.command("show")
def provider_show(
    name: str = typer.Argument(..., help="Provider name."),
    reveal_token: bool = typer.Option(False, "--reveal-token", help="Show plaintext token."),
) -> None:
    """Show configuration for a provider (token redacted by default)."""
    from leitum.commands.provider import run_provider_show

    run_provider_show(name, reveal_token=reveal_token)


@provider_app.command("add")
def provider_add() -> None:
    """Interactively add a new provider."""
    from leitum.commands.provider import run_provider_add

    run_provider_add()


@provider_app.command("remove")
def provider_remove(
    name: str = typer.Argument(..., help="Provider name to remove."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Remove a provider (with confirmation)."""
    from leitum.commands.provider import run_provider_remove

    run_provider_remove(name, yes=yes)
