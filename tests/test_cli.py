from __future__ import annotations

import pytest

from call_summariser import cli
from call_summariser.processor import BatchResult, FileFailure


class FakeGemini:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def generate(self, prompt: str) -> str:
        return "unused"


def base_args(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    return [
        "--in-dir",
        str(input_dir),
        "--out-dir",
        str(output_dir),
        "--company-name",
        "Acme",
        "--model",
        "gemini-model",
    ]


def test_main_success(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "load_dotenv_if_available", lambda: None)
    monkeypatch.setattr(cli, "GeminiLLM", FakeGemini)
    monkeypatch.setattr(
        cli,
        "process_directory",
        lambda **kwargs: BatchResult(processed=2, failed=0, skipped=1, failures=()),
    )

    assert cli.main(base_args(tmp_path)) == 0
    assert "processed=2 failed=0 skipped=1" in capsys.readouterr().out


def test_main_returns_one_and_reports_per_file_failures(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "load_dotenv_if_available", lambda: None)
    monkeypatch.setattr(cli, "GeminiLLM", FakeGemini)
    failure = FileFailure("bad.txt", "RuntimeError", "bad output")
    monkeypatch.setattr(
        cli,
        "process_directory",
        lambda **kwargs: BatchResult(processed=1, failed=1, skipped=0, failures=(failure,)),
    )

    assert cli.main(base_args(tmp_path)) == 1
    captured = capsys.readouterr()
    assert "failed: bad.txt: RuntimeError: bad output" in captured.err


def test_main_returns_two_for_expected_batch_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "load_dotenv_if_available", lambda: None)
    monkeypatch.setattr(cli, "GeminiLLM", FakeGemini)

    def fail(**kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(cli, "process_directory", fail)
    assert cli.main(base_args(tmp_path)) == 2
    assert "error: missing" in capsys.readouterr().err


def test_main_returns_two_for_unexpected_sdk_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "load_dotenv_if_available", lambda: None)

    class BrokenGemini(FakeGemini):
        def __enter__(self):
            raise KeyError("boom")

    monkeypatch.setattr(cli, "GeminiLLM", BrokenGemini)
    assert cli.main(base_args(tmp_path)) == 2
    assert "KeyError" in capsys.readouterr().err


def test_main_uses_environment_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "load_dotenv_if_available", lambda: None)
    monkeypatch.setenv("CALL_SUMMARISER_COMPANY_NAME", "EnvCo")
    monkeypatch.setenv("CALL_SUMMARISER_MODEL", "env-model")
    seen = {}

    class RecordingGemini(FakeGemini):
        def __init__(self, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(cli, "GeminiLLM", RecordingGemini)
    monkeypatch.setattr(
        cli,
        "process_directory",
        lambda **kwargs: BatchResult(0, 0, 0, ()),
    )
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    args = ["--in-dir", str(input_dir), "--out-dir", str(tmp_path / "out")]

    assert cli.main(args) == 0
    assert seen["model"] == "env-model"


def test_main_requires_company_and_model(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "load_dotenv_if_available", lambda: None)
    monkeypatch.delenv("CALL_SUMMARISER_COMPANY_NAME", raising=False)
    monkeypatch.delenv("CALL_SUMMARISER_MODEL", raising=False)
    input_dir = tmp_path / "in"
    input_dir.mkdir()

    with pytest.raises(SystemExit) as exc:
        cli.main(["--in-dir", str(input_dir), "--out-dir", str(tmp_path / "out")])
    assert exc.value.code == 2


def test_positive_arg_types_reject_invalid_values():
    with pytest.raises(cli.argparse.ArgumentTypeError):
        cli._positive_int("0")
    with pytest.raises(cli.argparse.ArgumentTypeError):
        cli._positive_float("0")
