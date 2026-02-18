from __future__ import annotations

import contextlib
import io
from pathlib import Path

from call_summariser.golden_check import main


class FakeLLM:
    def generate(self, prompt: str) -> str:
        # IMPORTANT: headers must be standalone lines to satisfy validate_summary()
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
            "COMPANY_NAME: None\n"
            "Other: None\n"
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


def test_golden_check_requires_10_outputs_written(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()

    # Create 10 minimal transcripts that parse cleanly
    for i in range(10):
        (in_dir / f"t{i}.txt").write_text(
            "Caller: X\nDirection: Inbound\n\n[00:00] AGENT: Hi\n[00:01] CALLER: Hello\n",
            encoding="utf-8",
        )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # Force ONE write to fail by making the target path a directory
    (out_dir / "t9-summary.txt").mkdir()

    rc, out = run_main(
        ["--in-dir", str(in_dir), "--out-dir", str(out_dir), "--company-name", "COMPANY_NAME"],
        llm=FakeLLM(),
    )

    assert rc != 0
    assert "Expected 10 output files" in out

def test_golden_check_writes_10_outputs_on_success(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()

    for i in range(10):
        (in_dir / f"t{i}.txt").write_text(
            "Caller: X\n\n[00:00] AGENT: Hi\n[00:01] CALLER: Hello\n",
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
