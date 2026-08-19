from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from call_summariser.summariser import Summariser
from call_summariser.transcript_parser import parse_transcript


@dataclass(frozen=True, slots=True)
class FileFailure:
    filename: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class BatchResult:
    processed: int
    failed: int
    skipped: int
    failures: tuple[FileFailure, ...]


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def process_directory(
    *,
    input_dir: Path,
    output_dir: Path,
    summariser: Summariser,
    overwrite: bool = True,
    max_input_bytes: int = 5_000_000,
) -> BatchResult:
    input_dir = input_dir.expanduser()
    output_dir = output_dir.expanduser()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
    if max_input_bytes < 1:
        raise ValueError("max_input_bytes must be greater than zero.")

    if input_dir.resolve() == output_dir.resolve():
        raise ValueError("Input and output directories must be different.")

    inputs = sorted(
        (path for path in input_dir.glob("*.txt") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )
    if not inputs:
        raise FileNotFoundError(f"No .txt transcript files found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    processed = 0
    skipped = 0
    failures: list[FileFailure] = []

    for input_path in inputs:
        output_path = output_dir / f"{input_path.stem}-summary.txt"
        if output_path.exists() and not overwrite:
            skipped += 1
            continue

        try:
            size = input_path.stat().st_size
            if size > max_input_bytes:
                raise ValueError(
                    f"Input is {size} bytes, exceeding the {max_input_bytes}-byte limit."
                )
            raw = input_path.read_text(encoding="utf-8-sig")
            transcript = parse_transcript(raw)
            summary = summariser.summarise(transcript)
            _atomic_write_text(output_path, summary)
            processed += 1
        except Exception as exc:  # noqa: BLE001 - one bad file must not abort a batch
            failures.append(
                FileFailure(
                    filename=input_path.name,
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )

    return BatchResult(
        processed=processed,
        failed=len(failures),
        skipped=skipped,
        failures=tuple(failures),
    )
