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
