from types import SimpleNamespace

import pytest

from call_summariser.errors import ConfigurationError
from call_summariser.gemini_client import GeminiLLM


class Models:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.calls = 0

    def generate_content(self, *, model, contents):
        self.calls += 1
        outcome = next(self.outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return SimpleNamespace(text=outcome)


class Client:
    def __init__(self, outcomes):
        self.models = Models(outcomes)
        self.closed = False

    def close(self):
        self.closed = True


class HttpError(RuntimeError):
    def __init__(self, status_code, message="error"):
        super().__init__(message)
        self.status_code = status_code


def test_retries_retryable_status_and_succeeds():
    sleeps = []
    client = Client([HttpError(503), "ok"])
    llm = GeminiLLM(model="model", client=client, sleep=sleeps.append)

    assert llm.generate("prompt") == "ok"
    assert client.models.calls == 2
    assert len(sleeps) == 1


def test_does_not_retry_non_retryable_status():
    client = Client([HttpError(400)])
    llm = GeminiLLM(model="model", client=client, sleep=lambda _: None)

    with pytest.raises(HttpError):
        llm.generate("prompt")
    assert client.models.calls == 1


def test_honours_retry_after_text():
    error = HttpError(429, "Please retry in 2.5s")
    assert GeminiLLM._retry_after_seconds(error) == 2.5


def test_rejects_empty_model_and_prompt():
    with pytest.raises(ConfigurationError):
        GeminiLLM(model="", client=Client(["ok"]))
    llm = GeminiLLM(model="model", client=Client(["ok"]))
    with pytest.raises(ValueError):
        llm.generate("  ")


def test_context_manager_closes_client():
    client = Client(["ok"])
    with GeminiLLM(model="model", client=client):
        pass
    assert client.closed is True


def test_constructor_validates_attempts_and_timeout():
    with pytest.raises(ValueError, match="max_attempts"):
        GeminiLLM(model="model", client=Client(["ok"]), max_attempts=0)
    with pytest.raises(ValueError, match="timeout_s"):
        GeminiLLM(model="model", client=Client(["ok"]), timeout_s=0)


def test_constructor_requires_api_key_when_no_client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        GeminiLLM(model="model")


def test_status_and_message_retry_classification():
    class StringCodeError(RuntimeError):
        code = "429"

    assert GeminiLLM._status_code(StringCodeError()) == 429
    assert GeminiLLM._is_retryable(RuntimeError("connection reset by peer")) is True
    assert GeminiLLM._is_retryable(RuntimeError("invalid argument")) is False


def test_retry_after_prefers_numeric_header():
    error = RuntimeError("error")
    error.response = SimpleNamespace(headers={"retry-after": "3"})
    assert GeminiLLM._retry_after_seconds(error) == 3.0


def test_empty_response_is_rejected():
    llm = GeminiLLM(model="model", client=Client(["  "]))
    with pytest.raises(RuntimeError, match="empty text"):
        llm.generate("prompt")
