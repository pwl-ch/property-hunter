"""Command-line interface for PropertyHunter."""

import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

from property_hunter import __version__
from property_hunter.settings import get_settings

app = typer.Typer(
    name="property_hunter",
    help="Local-first property analysis assistant.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"property_hunter version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Run PropertyHunter local tools."""


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Bind host.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Bind port.")] = 8765,
) -> None:
    """Serve the local FastAPI orchestration API."""
    import uvicorn

    from property_hunter.adapters.api import create_app

    if host != "127.0.0.1":
        raise typer.BadParameter("PropertyHunter only binds to 127.0.0.1 by default.")
    settings = get_settings().model_copy(update={"host": host, "port": port})
    uvicorn.run(create_app(settings), host=host, port=port)


@app.command()
def dashboard() -> None:
    """Launch the local Streamlit dashboard."""
    dashboard_path = Path(__file__).parent / "adapters" / "dashboard.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
        check=False,
    )


@app.command()
def export(
    format_: Annotated[
        str,
        typer.Option("--format", help="Export format: kml or csv."),
    ],
    output: Annotated[Path, typer.Option(help="Output file path.")],
) -> None:
    """Export stored properties as KML or CSV."""
    from property_hunter.adapters.sqlite import SQLitePropertyRepository
    from property_hunter.domain.export import properties_to_csv, properties_to_kml

    repository = SQLitePropertyRepository(get_settings().db_path)
    properties = repository.list(limit=1000)
    match format_.lower():
        case "kml":
            content = properties_to_kml(properties)
        case "csv":
            content = properties_to_csv(properties)
        case _:
            raise typer.BadParameter("format must be kml or csv")
    output.write_text(content, encoding="utf-8")
    typer.echo(f"Exported {len(properties)} properties to {output}")


@app.command()
def userscript(output: Annotated[Path | None, typer.Option()] = None) -> None:
    """Print or write the browser userscript."""
    from property_hunter.adapters.userscript import render_userscript

    userscript_source = render_userscript(get_settings())
    if output is None:
        typer.echo(userscript_source)
        return
    output.write_text(userscript_source, encoding="utf-8")
    typer.echo(f"Wrote userscript to {output}")


if __name__ == "__main__":
    app()
