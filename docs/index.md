# Property hunter

Property hunter

## Installation

Install using pip:

```bash
pip install property_hunter
```

Or using uv (recommended):

```bash
uv add property_hunter
```

## Quick Start

```python
import property_hunter

print(property_hunter.__version__)
```

### Command Line Interface

Property hunter provides a command-line interface:

```bash
# Show version
property_hunter --version

# Serve the local API
property_hunter serve

# Print the browser userscript
property_hunter userscript
```

### Local LLM

By default, analysis uses Pydantic AI with an LM Studio server at
`http://127.0.0.1:1234/v1` and model `google/gemma-4-e4b`. See
[Local LLM Agents](agents.md) for setup and offline mode.

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/pwl-ch/property-hunter.git
cd property-hunter
uv sync --group dev
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run ty check
```

### Prek Hooks

Install prek hooks:

```bash
prek install
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/pwl-ch/property-hunter/blob/main/LICENSE) file for details.
