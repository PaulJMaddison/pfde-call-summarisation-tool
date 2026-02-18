from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from call_summariser.golden_check import main


class FakeLLM:
    def generate(self, prompt: str) -> str:
        return (
            "Caller:\n"
            "John Doe, Unknown relationship, Inbound\n"
            "Subject:\n"
            "Test subject\n"
            "Executive Summary:\n"
            "Test executive summary.\n"
            "- Key point one\n"
            "- Key point two\n"
            "Next Steps:\n"
            "- COMPANY_NAME: None\n"
            "- Other: None\n"
        )


def run_main(argv: list[str], *, llm: object | None = None) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = main(argv, llm=llm)
    return rc, buf.getvalue()


def test_golden_check_fails_when_no_transcripts(tmp_path: Path) -> None:
    empty_in = tmp_path / "empty"
    empty_in.mkdir()

    out_dir = tmp_path / "out"

    rc, out = run_main(
        ["--in-dir", str(empty_in), "--out-dir", str(out_dir), "--company-name", "COMPANY_NAME"],
        llm=FakeLLM(),
    )

    assert rc != 0
    assert "No .txt transcripts found" in out


def test_golden_check_requires_10_transcripts(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()

    (in_dir / "t1.txt").write_text(
        "Caller: X\nDirection: Inbound\n\n[00:00] AGENT: Hi\n", encoding="utf-8"
    )

    out_dir = tmp_path / "out"

    rc, out = run_main(
        ["--in-dir", str(in_dir), "--out-dir", str(out_dir), "--company-name", "COMPANY_NAME"],
        llm=FakeLLM(),
    )

    assert rc != 0
    assert "Expected 10 transcripts" in out


def test_golden_check_writes_10_outputs_on_success(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()

    for i in range(10):
        (in_dir / f"t{i}.txt").write_text(
            "Caller: X\nDirection: Inbound\n\n[00:00] AGENT: Hi\n[00:01] CALLER: Hello\n",
            encoding="utf-8",
        )

    out_dir = tmp_path / "out"

    rc, out = run_main(
        ["--in-dir", str(in_dir), "--out-dir", str(out_dir), "--company-name", "COMPANY_NAME"],
        llm=FakeLLM(),
    )

    assert rc == 0, out
    outputs = sorted(out_dir.glob("*-summary.txt"))
    assert len(outputs) == 10


def test_golden_check_fails_if_not_all_outputs_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    RED test (should FAIL right now):

    Simulate one output write failing. golden_check should detect fewer than 10 outputs
    exist at the end and print "Expected 10 output files" + return non-zero.
    """

    in_dir = tmp_path / "in"
    in_dir.mkdir()

    for i in range(10):
        (in_dir / f"t{i}.txt").write_text(
            "Caller: X\nDirection: Inbound\n\n[00:00] AGENT: Hi\n[00:01] CALLER: Hello\n",
            encoding="utf-8",
        )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # IMPORTANT: patch the concrete path class (WindowsPath/PosixPath),
    # not pathlib.Path, otherwise it won't intercept on Windows.
    path_cls = type(out_dir)

    real_write_text = path_cls.write_text  # bound descriptor on the concrete class
    calls = {"n": 0}

    def flaky_write_text(self: Path, data: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        # Fail exactly one of the summary writes
        if self.name.endswith("-summary.txt") and calls["n"] == 5:
            raise OSError("simulated write failure")
        return real_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(path_cls, "write_text", flaky_write_text)

    rc, out = run_main(
        ["--in-dir", str(in_dir), "--out-dir", str(out_dir), "--company-name", "COMPANY_NAME"],
        llm=FakeLLM(),
    )

    # This is the new behaviour we want from golden_check.py (so it should be RED right now)
    assert rc != 0
    assert "Expected 10 output files" in out
