"""Typer-based CLI entry point for LAM."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from lam import config as cfg
from lam.pack import packager, par2, validator

app = typer.Typer(
    name="lam",
    help="Langzeitarchiv-Manager – long-term digital archiving tool.",
    no_args_is_help=True,
)

console = Console()

# ---------------------------------------------------------------------------
# lam pack
# ---------------------------------------------------------------------------


@app.command("pack")
def pack(
    source_dir: Annotated[Path, typer.Argument(help="Source directory to archive.")],
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Archive format: tar, iso, or dmg."),
    ] = "",
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory for archive + PAR2 files."),
    ] = None,
    redundancy: Annotated[
        Optional[int],
        typer.Option("--redundancy", "-r", help="PAR2 redundancy in percent (e.g. 15)."),
    ] = None,
    par2_volumes: Annotated[
        Optional[int],
        typer.Option("--par2-volumes", "-n", help="Number of PAR2 volume files (default: 1)."),
    ] = None,
) -> None:
    """Pack SOURCE_DIR into an archive and create PAR2 redundancy data."""
    # --- Resolve defaults from config ---
    if not fmt:
        fmt = str(cfg.get("pack.default_format") or "tar")
    if fmt not in ("tar", "iso", "dmg"):
        console.print(f"[red]Unknown format: {fmt!r}. Choose tar, iso, or dmg.[/red]")
        raise typer.Exit(code=1)

    if output is None:
        raw_output = cfg.get("pack.output_dir") or str(Path.home() / "LAM" / "staging")
        output = Path(str(raw_output)).expanduser()

    if redundancy is None:
        redundancy = int(cfg.get("pack.redundancy_percent"))

    if par2_volumes is None:
        par2_volumes = int(cfg.get("pack.par2_volumes"))

    # --- Validate ---
    console.print(f"[bold]Validating[/bold] {source_dir} …")
    try:
        validator.validate(source_dir)
    except validator.ValidationError as exc:
        console.print(f"[red]Validation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print("[green]✓ Validation passed.[/green]")

    # --- Pack ---
    console.print(f"[bold]Creating {fmt.upper()} archive[/bold] in {output} …")
    try:
        archive_path = packager.create_archive(source_dir, output, fmt=fmt)  # type: ignore[arg-type]
    except packager.PackagerError as exc:
        console.print(f"[red]Packaging failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    archive_size = archive_path.stat().st_size
    console.print(f"[green]✓ Archive created:[/green] {archive_path} ({_human_size(archive_size)})")

    # --- PAR2 ---
    console.print(f"[bold]Creating PAR2 redundancy data[/bold] ({redundancy}%) …")
    try:
        par2_files = par2.create(archive_path, redundancy, par2_volumes)
    except par2.Par2Error as exc:
        console.print(f"[red]PAR2 creation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    par2_size = sum(p.stat().st_size for p in par2_files)
    console.print(
        f"[green]✓ PAR2 files created:[/green] {len(par2_files)} file(s) "
        f"({_human_size(par2_size)})"
    )

    # --- Summary ---
    console.print()
    table = Table(title="Summary", show_header=True, header_style="bold cyan")
    table.add_column("File")
    table.add_column("Size", justify="right")
    table.add_row(str(archive_path.name), _human_size(archive_size))
    for p in par2_files:
        table.add_row(str(p.name), _human_size(p.stat().st_size))
    table.add_row("[bold]Total[/bold]", _human_size(archive_size + par2_size), style="bold")
    console.print(table)
    console.print(f"[bold green]Done.[/bold green] Redundancy: {redundancy}%")


# ---------------------------------------------------------------------------
# lam config
# ---------------------------------------------------------------------------

config_app = typer.Typer(help="Manage LAM configuration.")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key (e.g. pack.redundancy_percent).")],
    value: Annotated[str, typer.Argument(help="Value to set.")],
) -> None:
    """Set a configuration value."""
    cfg.set_value(key, value)
    console.print(f"[green]✓ Set[/green] {key} = {value!r}")


@config_app.command("get")
def config_get(
    key: Annotated[str, typer.Argument(help="Config key to retrieve.")],
) -> None:
    """Get a configuration value."""
    value = cfg.get(key)
    if value is None:
        console.print(f"[yellow]Key not found:[/yellow] {key}")
        raise typer.Exit(code=1)
    console.print(f"{key} = {value!r}")


@config_app.command("list")
def config_list() -> None:
    """List all configuration values."""
    data = cfg.list_all()
    table = Table(title="LAM Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Key")
    table.add_column("Value")
    _flatten_table(table, data)
    console.print(table)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def _flatten_table(table: Table, data: dict, prefix: str = "") -> None:
    for key, value in data.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            _flatten_table(table, value, full_key)
        else:
            table.add_row(full_key, str(value))
