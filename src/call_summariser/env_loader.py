from __future__ import annotations

from dotenv import load_dotenv


def load_dotenv_if_available() -> None:
    """Load a local .env file without overriding already configured environment variables."""
    load_dotenv(override=False)
