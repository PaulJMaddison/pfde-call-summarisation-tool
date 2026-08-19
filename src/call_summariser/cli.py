from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from call_summariser.env_loader import load_dotenv_if_available
from call_summariser.errors import CallSummariserError
from call_summariser.gemini_client import GeminiLLM
from call_summariser.processor import process_directory
from call_summariser.summariser import Summariser


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="call-summariser",
        description="Generate validated insurance call summaries from transcript text files.",
    )
    parser.add_argument(
        "--in-dir", type=Path, required=True, help="Directory containing .txt files"
    )
    parser.add_argument(
        "--out-dir", type=Path, required=True, help="Directory for generated summaries"
    )
    parser.add_argument("--company-name", help="Company label used in Next Steps")
    parser.add_argument("--model", help="Gemini model identifier")
    parser.add_argument("--max-chars", type=_positive_int, default=1500)
    parser.add_argument("--summary-attempts", type=_positive_int, default=3)
    parser.add_argument("--request-attempts", type=_positive_int, default=4)
    parser.add_argument("--request-timeout", type=_positive_float, default=30.0, metavar="SECONDS")
    parser.add_argument("--max-input-bytes", type=_positive_int, default=5_000_000)
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip output files that already exist instead of replacing them",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_available()
    parser = build_parser()
    args = parser.parse_args(argv)

    company_name = (args.company_name or os.getenv("CALL_SUMMARISER_COMPANY_NAME", "")).strip()
    model = (args.model or os.getenv("CALL_SUMMARISER_MODEL", "")).strip()
    if not company_name:
        parser.error("--company-name or CALL_SUMMARISER_COMPANY_NAME is required")
    if not model:
        parser.error("--model or CALL_SUMMARISER_MODEL is required")

    try:
        with GeminiLLM(
            model=model,
            max_attempts=args.request_attempts,
            timeout_s=args.request_timeout,
        ) as llm:
            summariser = Summariser(
                llm=llm,
                company_name=company_name,
                max_attempts=args.summary_attempts,
                max_chars=args.max_chars,
            )
            result = process_directory(
                input_dir=args.in_dir,
                output_dir=args.out_dir,
                summariser=summariser,
                overwrite=not args.no_overwrite,
                max_input_bytes=args.max_input_bytes,
            )
    except (CallSummariserError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    for failure in result.failures:
        print(
            f"failed: {failure.filename}: {failure.error_type}: {failure.message}",
            file=sys.stderr,
        )

    print(
        f"processed={result.processed} failed={result.failed} skipped={result.skipped}",
        file=sys.stdout,
    )
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
