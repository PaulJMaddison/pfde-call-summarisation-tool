import pytest

from call_summariser.errors import TranscriptParseError
from call_summariser.transcript_parser import parse_transcript


def test_parses_realistic_tsv_export():
    raw = """Interaction Type:\tCall
Interaction ID:\tABC-001
Direction:\tInbound

Date/Time\tParticipant Type\tParticipant\tText
00:02\tInternal\tSarah Mitchell\tGood morning, claims team.
00:06\tExternal\tUnavailable\tHi, my name is David Chen.
"""
    transcript = parse_transcript(raw)

    assert transcript.metadata["Interaction Type"] == "Call"
    assert transcript.metadata["Interaction ID"] == "ABC-001"
    assert transcript.metadata["Direction"] == "Inbound"
    assert len(transcript.lines) == 2
    assert transcript.lines[0].timestamp == "00:02"
    assert transcript.lines[0].speaker == "Sarah Mitchell"
    assert transcript.lines[1].text == "Hi, my name is David Chen."


def test_parses_bracket_format_and_continuations():
    raw = """Direction: Outbound

[00:00] AGENT: First line
continued sentence
[00:03] CALLER: Reply
"""
    transcript = parse_transcript(raw)
    assert transcript.metadata == {"Direction": "Outbound"}
    assert len(transcript.lines) == 2
    assert transcript.lines[0].text == "First line continued sentence"


def test_handles_utf8_bom_and_null_characters():
    transcript = parse_transcript("\ufeff[00:00] CALLER: Hel\x00lo\n")
    assert transcript.lines[0].text == "Hello"


@pytest.mark.parametrize("raw", ["", "   \n", "Caller: Nobody\nDirection: Inbound\n"])
def test_rejects_inputs_without_dialogue(raw):
    with pytest.raises(TranscriptParseError):
        parse_transcript(raw)
