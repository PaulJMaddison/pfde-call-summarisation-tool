from __future__ import annotations

import contextlib
import io
from pathlib import Path

from tools.golden_check import main


class FakeLLM:
    def generate(self, prompt: str) -> str:
        # Minimal valid summary that should pass your validators
        return (
            "Caller: John Doe, Unknown relationship, Inbound\n"
            "Subject:\nTest call\n"
            "Executive Summary:\nTest.\n"
            "- A\n"
            "- B\n"
            "Next Steps:\n"
            "COMPANY_NAME: None\n"
            "Other: None\n"
        )


def run_main(argv: list[str], *, llm: object | None = None) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
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

    # create only 1 transcript to simulate wrong input set
    (in_dir / "t1.txt").write_text("Caller: X\n\n[00:00] AGENT: Hi\n", encoding="utf-8")

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

    # create 10 transcripts
    for i in range(10):
        (in_dir / f"t{i}.txt").write_text(
            "Caller: X\n\n[00:00] AGENT: Hi\n[00:01] CALLER: Hello\n", encoding="utf-8"
        )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # Force one write to fail by creating a directory where a file should be written
    (out_dir / "t9-summary.txt").mkdir()

    rc, out = run_main(
        ["--in-dir", str(in_dir), "--out-dir", str(out_dir), "--company-name", "COMPANY_NAME"],
        llm=FakeLLM(),
    )

    # This SHOULD be RED right now (golden_check currently doesn't enforce output count)
    assert rc != 0
    assert "Expected 10 output files" in out
