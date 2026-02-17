import pytest

from call_summariser.summariser import Summariser
from call_summariser.transcript_parser import Transcript, TranscriptLine


class FakeLLMTooLongThenOk:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return (
                "Caller:\nX\nSubject:\nY\nExecutive Summary:\n"
                + ("a" * 1600)
                + "\nNext Steps:\n- COMPANY_NAME: A\n- Other: None\n"
            )
        return (
            "Caller:\nX\nSubject:\nY\nExecutive Summary:\nOK\n- Detail\n"
            "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
        )


def test_retries_when_first_output_too_long():
    t = Transcript(metadata={}, lines=[TranscriptLine("00:00", "CALLER", "Hello")])
    s = Summariser(llm=FakeLLMTooLongThenOk(), company_name="COMPANY_NAME", max_attempts=2)
    out = s.summarise(t)
    assert "Executive Summary:" in out


class FakeLLMBadOptional:
    def generate(self, prompt: str) -> str:
        return (
            "Caller:\nX\nSubject:\nY\nExecutive Summary:\nOK\n"
            "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
            "Injury:\nNone\n"
        )


def test_fails_if_optional_section_not_supported():
    t = Transcript(metadata={}, lines=[TranscriptLine("00:00", "CALLER", "Repairs only")])
    s = Summariser(llm=FakeLLMBadOptional(), company_name="COMPANY_NAME", max_attempts=1)
    with pytest.raises(RuntimeError):
        s.summarise(t)
