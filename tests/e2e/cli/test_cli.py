"""End-to-end tests for CLI commands."""

from typer.testing import CliRunner

from property_hunter import __version__
from property_hunter.cli import app

runner = CliRunner()


def test_version() -> None:
    """Expose the package version."""
    # given
    version = __version__

    # when
    has_version = bool(version)

    # then
    assert has_version


def test_cli_version() -> None:
    """Print the CLI version."""
    # given
    command = ["--version"]

    # when
    result = runner.invoke(app, command)

    # then
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_userscript_prints_capture_button() -> None:
    """Print the generated userscript from the CLI."""
    # given
    command = ["userscript"]

    # when
    result = runner.invoke(app, command)

    # then
    assert result.exit_code == 0
    assert "Analizuj w PropertyHunter" in result.stdout
    assert "127.0.0.1:8765/api/analyze" in result.stdout
