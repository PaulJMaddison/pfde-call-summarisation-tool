from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TranscriptLine:
    timestamp: str
    speaker: str
    text: str


@dataclass(frozen=True)
class Transcript:
    metadata: Dict[str, str]
    lines: List[TranscriptLine]


def parse_transcript(raw: str) -> Transcript:
    metadata: Dict[str, str] = {}
    lines: List[TranscriptLine] = []

    in_body = False
    for line in raw.splitlines():
        stripped = line.strip()

        if not in_body:
            if stripped.startswith("[") and "]" in stripped:
                in_body = True
            elif stripped == "":
                in_body = True
                continue
            else:
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    metadata[k.strip()] = v.strip()
                continue

        if stripped == "":
            continue

        if not stripped.startswith("[") or "]" not in stripped:
            if lines:
                last = lines[-1]
                lines[-1] = TranscriptLine(
                    last.timestamp, last.speaker, f"{last.text} {stripped}".strip()
                )
            else:
                lines.append(TranscriptLine("??:??", "UNKNOWN", stripped))
            continue

        ts_part, rest = stripped.split("]", 1)
        timestamp = ts_part.lstrip("[").strip()
        rest = rest.strip()

        if ":" in rest:
            speaker, text = rest.split(":", 1)
            lines.append(TranscriptLine(timestamp, speaker.strip(), text.strip()))
        else:
            lines.append(TranscriptLine(timestamp, "UNKNOWN", rest.strip()))

    return Transcript(metadata=metadata, lines=lines)
