from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_golden_check_fails_when_no_transcripts(tmp_path: Path) -> None:
    empty_in = tmp_path / "empty"
    empty_in.mkdir()

    out_dir = tmp_path / "out"

    proc = subprocess.run(
        [
            sys.executable,
            "tools/golden_check.py",
            "--in-dir",
            str(empty_in),
            "--out-dir",
            str(out_dir),
            "--company-name",
            "COMPANY_NAME",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "No .txt transcripts found" in (proc.stdout + proc.stderr)

def test_golden_check_requires_10_transcripts(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    # create only 1 transcript to simulate wrong input set
    (in_dir / "t1.txt").write_text("Caller: X\n\n[00:00] AGENT: Hi\n", encoding="utf-8")

    out_dir = tmp_path / "out"

    proc = subprocess.run(
        [
            sys.executable,
            "tools/golden_check.py",
            "--in-dir",
            str(in_dir),
            "--out-dir",
            str(out_dir),
            "--company-name",
            "COMPANY_NAME",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0
    assert "Expected 10 transcripts" in (proc.stdout + proc.stderr)

