from __future__ import annotations

import argparse
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from call_summariser.optional_gating import validate_optional_sections_against_transcript
from call_summariser.summariser import Summariser
from call_summariser.summary_validator import validate_summary
from call_summariser.transcript_parser import parse_transcript

EXPECTED_TRANSCRIPTS = 10


class LLM(Protocol):
    def generate(self, prompt: str) -> str: ...


def _enforce_output_count(out_dir: Path) -> int | None:
    written = len(list(out_dir.glob("*-summary.txt")))
    if written != EXPECTED_TRANSCRIPTS:
        print(f"Expected {EXPECTED_TRANSCRIPTS} output files, wrote {written} in: {out_dir.resolve()}")
        return 2
    return None


def main(argv: list[str] | None = None, *, llm: LLM | None = None) -> int:
    load_dotenv()

    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--company-name", type=str, default="COMPANY_NAME")
    p.add_argument("--model", type=str, default="gemini-3-flash-preview")
    args = p.parse_args(argv)

    inputs = sorted(args.in_dir.glob("*.txt"))
    if not inputs:
        print(f"No .txt transcripts found in: {args.in_dir.resolve()}")
        return 2

    if len(inputs) != EXPECTED_TRANSCRIPTS:
        print(f"Expected {EXPECTED_TRANSCRIPTS} transcripts, found {len(inputs)} in: {args.in_dir.resolve()}")
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if llm is None:
        from call_summariser.gemini_client import GeminiLLM

        llm = GeminiLLM(model=args.model)

    summariser = Summariser(llm=llm, company_name=args.company_name, max_attempts=2)

    failures: list[str] = []
    retries_report: list[str] = []

    for fp in inputs:
        raw = fp.read_text(encoding="utf-8")
        t = parse_transcript(raw)

        try:
            result = summariser.summarise_with_result(t)
            summary = result.summary

            validate_summary(summary, company_name=args.company_name)
            transcript_text = "\n".join(f"{line.speaker}: {line.text}" for line in t.lines)
            validate_optional_sections_against_transcript(summary, transcript_text)

            out_fp = args.out_dir / f"{fp.stem}-summary.txt"
            out_fp.write_text(summary, encoding="utf-8")

            if result.attempts_used > 1:
                retries_report.append(f"{fp.name}: attempts_used={result.attempts_used}")

        except Exception as e:
            failures.append(f"{fp.name}: {type(e).__name__}: {e}")

    if retries_report:
        print("RETRIES USED:")
        for line in retries_report:
            print(f"  - {line}")
        print()

    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")

        rc = _enforce_output_count(args.out_dir)
        if rc is not None:
            return rc

        return 1

    rc = _enforce_output_count(args.out_dir)
    if rc is not None:
        return rc

    print("Golden check PASSED: all transcripts summarised and validated.")
    return 0
