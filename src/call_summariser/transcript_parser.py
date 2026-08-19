from __future__ import annotations

import re
from dataclasses import dataclass

from call_summariser.errors import TranscriptParseError

_BRACKET_LINE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s*(?P<speaker>[^:]+):\s*(?P<text>.*)$"
)


@dataclass(frozen=True, slots=True)
class TranscriptLine:
    timestamp: str
    speaker: str
    text: str


@dataclass(frozen=True, slots=True)
class Transcript:
    metadata: dict[str, str]
    lines: list[TranscriptLine]


def _metadata_pair(line: str) -> tuple[str, str] | None:
    if "\t" in line:
        parts = [part.strip() for part in line.split("\t")]
        if len(parts) >= 2 and parts[0].endswith(":"):
            key = parts[0].rstrip(":").strip()
            value = "\t".join(parts[1:]).strip()
            if key:
                return key, value

    if ":" in line:
        key, value = line.split(":", 1)
        key = key.strip()
        if key and not key.startswith("["):
            return key, value.strip()
    return None


def _is_tsv_header(line: str) -> bool:
    cells = [cell.strip().casefold() for cell in line.split("\t")]
    return len(cells) >= 4 and "date/time" in cells and "participant" in cells and "text" in cells


def _parse_tsv_dialogue(line: str) -> TranscriptLine | None:
    parts = [part.strip() for part in line.split("\t")]
    if len(parts) < 4:
        return None

    timestamp, participant_type, participant = parts[:3]
    text = "\t".join(parts[3:]).strip()
    if not timestamp or not text:
        return None

    speaker = participant or participant_type or "UNKNOWN"
    return TranscriptLine(timestamp=timestamp, speaker=speaker, text=text)


def parse_transcript(raw: str) -> Transcript:
    """Parse supported transcript text into metadata and dialogue lines.

    Supported body formats are:
    - tab-separated exports with Date/Time, Participant Type, Participant and Text columns
    - bracketed lines such as ``[00:03] CALLER: Hello``

    Non-structured lines after dialogue has started are treated as continuations of the
    preceding utterance. Empty or non-dialogue inputs fail explicitly instead of being
    sent to an LLM as a misleading transcript.
    """
    if not isinstance(raw, str):
        raise TranscriptParseError("Transcript input must be text.")

    raw = raw.lstrip("\ufeff").replace("\x00", "")
    if not raw.strip():
        raise TranscriptParseError("Transcript is empty.")

    metadata: dict[str, str] = {}
    lines: list[TranscriptLine] = []
    body_started = False
    tsv_mode = False

    for original_line in raw.splitlines():
        stripped = original_line.strip()
        if not stripped:
            if metadata and not body_started:
                body_started = True
            continue

        if _is_tsv_header(original_line):
            body_started = True
            tsv_mode = True
            continue

        bracket_match = _BRACKET_LINE.match(stripped)
        if bracket_match:
            body_started = True
            tsv_mode = False
            lines.append(
                TranscriptLine(
                    timestamp=bracket_match.group("timestamp").strip(),
                    speaker=bracket_match.group("speaker").strip() or "UNKNOWN",
                    text=bracket_match.group("text").strip(),
                )
            )
            continue

        if not body_started:
            pair = _metadata_pair(original_line)
            if pair is not None:
                key, value = pair
                metadata[key] = value
                continue

        if tsv_mode:
            parsed = _parse_tsv_dialogue(original_line)
            if parsed is not None:
                lines.append(parsed)
                continue

        if lines:
            previous = lines[-1]
            continuation = stripped
            lines[-1] = TranscriptLine(
                timestamp=previous.timestamp,
                speaker=previous.speaker,
                text=f"{previous.text} {continuation}".strip(),
            )
            continue

        pair = _metadata_pair(original_line)
        if pair is not None and not body_started:
            key, value = pair
            metadata[key] = value

    usable_lines = [line for line in lines if line.text.strip()]
    if not usable_lines:
        raise TranscriptParseError(
            "No dialogue lines were found. Expected a tab-separated transcript export "
            "or lines in '[timestamp] SPEAKER: text' format."
        )

    return Transcript(metadata=metadata, lines=usable_lines)
