from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from call_summariser.errors import SummaryGenerationError, SummaryValidationError
from call_summariser.prompting import build_prompt, build_retry_prompt
from call_summariser.run_result import RunResult
from call_summariser.summary_validator import validate_summary
from call_summariser.transcript_parser import Transcript


class LLM(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True, slots=True)
class Summariser:
    llm: LLM
    company_name: str
    max_attempts: int = 3
    max_chars: int = 1500

    def __post_init__(self) -> None:
        company_name = self.company_name.strip()
        if not company_name:
            raise ValueError("company_name must not be empty.")
        if "\n" in company_name or "\r" in company_name:
            raise ValueError("company_name must be a single line.")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
        if self.max_chars < 200:
            raise ValueError("max_chars must be at least 200.")
        object.__setattr__(self, "company_name", company_name)

    def summarise_with_result(self, transcript: Transcript) -> RunResult:
        if not transcript.lines:
            raise ValueError("Transcript contains no dialogue lines.")

        base_prompt = build_prompt(
            transcript,
            company_name=self.company_name,
            max_chars=self.max_chars,
        )
        prompt = base_prompt
        last_error: SummaryValidationError | None = None

        for attempt in range(1, self.max_attempts + 1):
            generated = self.llm.generate(prompt)
            output = (generated or "").strip()
            if output and len(output) < self.max_chars:
                output += "\n"

            try:
                validate_summary(
                    output,
                    company_name=self.company_name,
                    max_chars=self.max_chars,
                )
                return RunResult(summary=output, attempts_used=attempt)
            except SummaryValidationError as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    prompt = build_retry_prompt(
                        base_prompt,
                        previous_output=output or "<empty>",
                        validation_error=str(exc),
                    )

        message = "Unable to produce a valid summary"
        if last_error is not None:
            message += f" after {self.max_attempts} attempt(s): {last_error}"
        raise SummaryGenerationError(message) from last_error

    def summarise(self, transcript: Transcript) -> str:
        return self.summarise_with_result(transcript).summary
