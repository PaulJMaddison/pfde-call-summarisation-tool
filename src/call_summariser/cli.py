from __future__ import annotations

import argparse
from pathlib import Path

from call_summariser.env_loader import load_dotenv_if_available
from call_summariser.gemini_client import GeminiLLM
from call_summariser.summariser import Summariser
from call_summariser.transcript_parser import parse_transcript


def main() -> int:
    load_dotenv_if_available()

    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--company-name", type=str, default="COMPANY_NAME")
    p.add_argument("--model", type=str, default="gemini-3-flash-preview")
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    llm = GeminiLLM(model=args.model)
    summariser = Summariser(llm=llm, company_name=args.company_name)

    for fp in sorted(args.in_dir.glob("*.txt")):
        raw = fp.read_text(encoding="utf-8")
        t = parse_transcript(raw)
        summary = summariser.summarise(t)
        (args.out_dir / f"{fp.stem}-summary.txt").write_text(summary, encoding="utf-8")

    return 0
