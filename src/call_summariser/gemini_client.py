from __future__ import annotations

import os
import random
import re
import time
from collections.abc import Callable
from typing import Any

from call_summariser.errors import ConfigurationError

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class GeminiLLM:
    """Small resilient adapter around the Google Gen AI Python SDK."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        max_attempts: int = 4,
        timeout_s: float = 30.0,
        client: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        model = model.strip()
        if not model:
            raise ConfigurationError("A Gemini model name is required.")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be greater than zero.")

        self.model = model
        self.max_attempts = max_attempts
        self.timeout_s = timeout_s
        self._sleep = sleep

        if client is not None:
            self._client = client
            return

        resolved_api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        if not resolved_api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY is not set. Set it in the environment or a local .env file."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ConfigurationError(
                "The Google Gen AI SDK is not installed. Install the package dependencies first."
            ) from exc

        self._client = genai.Client(
            api_key=resolved_api_key,
            http_options=types.HttpOptions(timeout=max(1, int(timeout_s * 1000))),
        )

    @staticmethod
    def _status_code(error: BaseException) -> int | None:
        for attribute in ("status_code", "code"):
            value = getattr(error, attribute, None)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
        return None

    @classmethod
    def _is_retryable(cls, error: BaseException) -> bool:
        status = cls._status_code(error)
        if status is not None:
            return status in _RETRYABLE_STATUS_CODES

        message = str(error).casefold()
        return any(
            marker in message
            for marker in (
                "resource_exhausted",
                "service_unavailable",
                "timed out",
                "timeout",
                "connection reset",
                "connection error",
                "temporarily unavailable",
            )
        )

    @staticmethod
    def _retry_after_seconds(error: BaseException) -> float | None:
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", None)
        if headers is not None:
            try:
                value = headers.get("retry-after")
                if value is not None:
                    return max(0.0, float(value))
            except (AttributeError, TypeError, ValueError):
                pass

        message = str(error)
        patterns = (
            r"retry\s+in\s+([0-9]+(?:\.[0-9]+)?)s",
            r"retryDelay[\"']?\s*:\s*[\"']?([0-9]+(?:\.[0-9]+)?)s",
        )
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    def _call_once(self, prompt: str) -> str:
        response = self._client.models.generate_content(model=self.model, contents=prompt)
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Gemini returned an empty text response.")
        return text

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be empty.")

        last_error: BaseException | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self._call_once(prompt)
            except Exception as exc:  # noqa: BLE001 - SDK error types vary by release
                last_error = exc
                if not self._is_retryable(exc) or attempt == self.max_attempts:
                    raise

                retry_after = self._retry_after_seconds(exc)
                if retry_after is None:
                    retry_after = min(1.5 ** (attempt - 1) + random.uniform(0.0, 0.5), 15.0)
                self._sleep(min(retry_after, 60.0))

        assert last_error is not None
        raise last_error

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> GeminiLLM:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
