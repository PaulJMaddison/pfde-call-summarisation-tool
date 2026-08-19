import pytest

from call_summariser.errors import SummaryGenerationError
from call_summariser.summariser import Summariser
from call_summariser.transcript_parser import Transcript, TranscriptLine

VALID = (
    "Caller:\nDavid, Unknown relationship\n"
    "Subject:\nClaim status\n"
    "Executive Summary:\nCaller requested a status update.\n"
    "Next Steps:\n- Acme: Contact caller.\n- Other: None\n"
)


class SequenceLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self.responses)


def transcript():
    return Transcript({}, [TranscriptLine("00:01", "David", "Can I get an update?")])


def test_retries_with_previous_output_and_validation_error():
    llm = SequenceLLM(["not valid", VALID])
    result = Summariser(llm=llm, company_name="Acme", max_attempts=2).summarise_with_result(
        transcript()
    )

    assert result.attempts_used == 2
    assert result.summary == VALID
    assert "<previous_output>\nnot valid\n</previous_output>" in llm.prompts[1]
    assert "failed validation" in llm.prompts[1]


def test_raises_after_attempt_budget_exhausted():
    llm = SequenceLLM(["bad", "still bad"])
    with pytest.raises(SummaryGenerationError, match="2 attempt"):
        Summariser(llm=llm, company_name="Acme", max_attempts=2).summarise(transcript())


def test_rejects_invalid_configuration():
    llm = SequenceLLM([VALID])
    with pytest.raises(ValueError):
        Summariser(llm=llm, company_name="", max_attempts=1)
    with pytest.raises(ValueError):
        Summariser(llm=llm, company_name="Acme", max_attempts=0)


def test_accepts_valid_output_exactly_at_character_limit():
    template = (
        "Caller:\nX\nSubject:\nY\nExecutive Summary:\n{}\n"
        "Next Steps:\n- Acme: None\n- Other: None"
    )
    max_chars = 200
    padding = "x" * (max_chars - len(template.format("")))
    generated = template.format(padding)
    assert len(generated) == max_chars

    result = Summariser(
        llm=SequenceLLM([generated]),
        company_name="Acme",
        max_attempts=1,
        max_chars=max_chars,
    ).summarise_with_result(transcript())

    assert result.summary == generated
    assert len(result.summary) == max_chars
