from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from call_summariser.optional_gating import validate_optional_sections_against_transcript
from call_summariser.prompting import build_prompt
from call_summariser.summary_validator import ValidationError, validate_summary
from call_summariser.transcript_parser import Transcript


class LLM(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class Summariser:
    llm: LLM
    company_name: str
    max_attempts: int = 2

    def summarise(self, t: Transcript) -> str:
        transcript_text = "\n".join(f"{l.speaker}: {l.text}" for l in t.lines)
        prompt = build_prompt(t, company_name=self.company_name)

        last_err: Exception | None = None
        for _ in range(self.max_attempts):
            out = (self.llm.generate(prompt) or "").strip() + "\n"
            try:
                validate_summary(out, company_name=self.company_name)
                validate_optional_sections_against_transcript(out, transcript_text)
                return out
            except (ValidationError, ValueError) as e:
                last_err = e
                prompt = (
                    prompt
                    + f"\nThe previous output violated constraints ({type(e).__name__}: {e}). "
                      "Rewrite concisely and comply exactly.\n"
                )

        raise RuntimeError(f"Failed to produce a valid summary: {last_err}")
