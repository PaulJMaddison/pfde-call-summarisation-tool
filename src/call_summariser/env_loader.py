from __future__ import annotations

import importlib
import importlib.util


def load_dotenv_if_available() -> None:
    """Load environment variables from a .env file when python-dotenv is installed."""
    if importlib.util.find_spec("dotenv") is None:
        return

    dotenv_module = importlib.import_module("dotenv")
    load_dotenv = getattr(dotenv_module, "load_dotenv", None)
    if callable(load_dotenv):
        load_dotenv()
