# Repository Guidelines

## Agent-Specific Instructions

When exiting plan mode, save the plan to `docs/<feature-name>/plan-<feature-name>.md`.

## Project Structure & Module Organization

This package uses the `src/` layout. Code lives in `src/property_hunter/`; the
Typer CLI is in `cli.py`. Tests live in `tests/`; shared fixtures belong in
`tests/conftest.py`. Docs live in `docs/` and build through `mkdocs.yml`.
Metadata, dependencies, and tool config are in `pyproject.toml`; common
workflows are in the root `Makefile`.

## Build, Test, and Development Commands

- `make install`: install dependencies with `uv sync --all-groups`.
- `make test`: run pytest verbosely.
- `make test-cov`: run tests with coverage reports.
- `make test-matrix`: run Hatch tests on Python 3.12 and 3.13.
- `make verify`: run lint, format check, and type checking without changing files.
- `make fix`: apply Ruff lint fixes and formatting.
- `make docs`: build MkDocs documentation.
- `make docs-serve`: serve docs locally.

Use `uv` for project management. Prefer `uv add`, `uv sync`, and `uv run <tool>`.

## Coding Style & Naming Conventions

Target Python 3.12+ and use modern typing: `list[str]`, `dict[str, int]`,
`str | None`, and `typing.Self` where appropriate. Keep code fully typed and
maintain `src/property_hunter/py.typed`. Ruff handles linting, import ordering,
and formatting with an 88-character line length. Use snake_case for modules,
functions, variables, and tests.

Each public function and class needs a concise NumPy-style docstring. Write for
new developers: explain what the API does, define important parameters and
return values, and avoid vague restatements. Be specific and value dense.

## Testing Guidelines

Start by writing or updating tests for intended behavior. Do not add trivial
tests that only repeat implementation details or assert imports. Tests use
pytest under `tests/`; name files `test_*.py` and functions `test_*`. Put shared
setup in `tests/conftest.py`. Use the `slow` marker for slower tests. Before a
pull request, make sure tests pass with `make test`; use `make test-matrix` when
Python-version behavior may differ.

## Commit & Pull Request Guidelines

The existing history is minimal, but `docs/contributing.md` specifies
Conventional Commits. Use messages such as `feat: add listing parser`,
`fix: handle empty CLI argument`, or `docs: update usage examples`.

Pull requests should include a clear description, linked issues when relevant,
tests for behavior changes, and docs updates for user-facing changes. Before
review, run `make verify` and make sure tests pass.

## Security & Configuration Tips

Do not commit secrets, local environment files, or generated coverage artifacts.
Run `make pysentry` when changing dependencies or packaging configuration.
