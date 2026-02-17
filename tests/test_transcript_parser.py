from call_summariser.transcript_parser import parse_transcript


def test_parse_transcript_extracts_metadata_and_lines():
    raw = """Caller: John Doe
Direction: Inbound
Claimant: Jane Doe

[00:00] AGENT: Hello, you're through to PFDE.
[00:03] CALLER: Hi, I'm calling about a crash yesterday.
"""
    t = parse_transcript(raw)

    assert t.metadata["Caller"] == "John Doe"
    assert t.metadata["Direction"] == "Inbound"
    assert len(t.lines) == 2
    assert t.lines[0].timestamp == "00:00"
    assert t.lines[0].speaker == "AGENT"
    assert "PFDE" in t.lines[0].text


def test_parse_transcript_tolerates_missing_metadata_block():
    raw = "[00:00] CALLER: Hello\n"
    t = parse_transcript(raw)
    assert t.metadata == {}
    assert len(t.lines) == 1


def test_parse_transcript_tolerates_malformed_body_lines_by_appending():
    raw = """Caller: X

[00:00] CALLER: First line
this is a continuation
"""
    t = parse_transcript(raw)
    assert len(t.lines) == 1
    assert "continuation" in t.lines[0].text
