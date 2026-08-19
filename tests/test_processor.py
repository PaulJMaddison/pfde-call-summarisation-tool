from pathlib import Path

import pytest

from call_summariser.processor import process_directory

SUMMARY = (
    "Caller:\nX\nSubject:\nY\nExecutive Summary:\nZ\n"
    "Next Steps:\n- Acme: None\n- Other: None\n"
)


class FakeSummariser:
    def summarise(self, transcript):
        if "FAIL" in transcript.lines[0].text:
            raise RuntimeError("synthetic failure")
        return SUMMARY


def write_bracket(path: Path, text: str):
    path.write_text(f"[00:00] CALLER: {text}\n", encoding="utf-8")


def test_batch_continues_after_one_file_fails(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    write_bracket(input_dir / "a.txt", "ok")
    write_bracket(input_dir / "b.txt", "FAIL")
    write_bracket(input_dir / "c.txt", "ok")

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        summariser=FakeSummariser(),
    )

    assert result.processed == 2
    assert result.failed == 1
    assert (output_dir / "a-summary.txt").read_text(encoding="utf-8") == SUMMARY
    assert not (output_dir / "b-summary.txt").exists()
    assert not list(output_dir.glob("*.tmp"))


def test_no_overwrite_skips_existing_output(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    write_bracket(input_dir / "a.txt", "ok")
    existing = output_dir / "a-summary.txt"
    existing.write_text("keep", encoding="utf-8")

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        summariser=FakeSummariser(),
        overwrite=False,
    )
    assert result.skipped == 1
    assert existing.read_text(encoding="utf-8") == "keep"


def test_rejects_same_input_and_output_directory(tmp_path):
    with pytest.raises(ValueError, match="must be different"):
        process_directory(
            input_dir=tmp_path,
            output_dir=tmp_path,
            summariser=FakeSummariser(),
        )


def test_rejects_oversized_file_without_writing_partial_output(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    write_bracket(input_dir / "a.txt", "too large")

    result = process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        summariser=FakeSummariser(),
        max_input_bytes=5,
    )
    assert result.failed == 1
    assert not (output_dir / "a-summary.txt").exists()


def test_batch_level_input_validation(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_directory(
            input_dir=tmp_path / "missing",
            output_dir=tmp_path / "out",
            summariser=FakeSummariser(),
        )

    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        process_directory(
            input_dir=file_path,
            output_dir=tmp_path / "out",
            summariser=FakeSummariser(),
        )

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="max_input_bytes"):
        process_directory(
            input_dir=empty,
            output_dir=tmp_path / "out",
            summariser=FakeSummariser(),
            max_input_bytes=0,
        )
    with pytest.raises(FileNotFoundError, match="No .txt"):
        process_directory(
            input_dir=empty,
            output_dir=tmp_path / "out",
            summariser=FakeSummariser(),
        )
