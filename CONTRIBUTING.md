# Contributing

Contributions are welcome.

## Local setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Activate the virtual environment using the command appropriate for your platform.

## Quality gate

Before opening a pull request, run:

```bash
ruff check .
mypy
pytest --cov=call_summariser --cov-report=term-missing
python -m build
```

Add regression coverage for behaviour changes. Prefer boundary, malformed-input, retry, state-transition, and failure-isolation coverage rather than only happy-path assertions.

## Pull requests

Keep pull requests focused, explain the user-facing behaviour change, and call out any compatibility or data-handling implications. Do not commit secrets, real customer transcripts, generated summaries, virtual environments, caches, or package build artefacts.
