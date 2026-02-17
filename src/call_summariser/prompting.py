from __future__ import annotations

from call_summariser.transcript_parser import Transcript


def build_prompt(t: Transcript, *, company_name: str) -> str:
    transcript_text = "\n".join(
        f"[{line.timestamp}] {line.speaker}: {line.text}" for line in t.lines
    )

    return f"""You are an expert insurance call summariser.

OUTPUT RULES (must follow exactly):
1) Use these exact headers as whole lines, in this exact order:
Caller:
Subject:
Executive Summary:
Next Steps:
2) Only include these optional sections IF clearly discussed in the transcript:
Liability Summary:
Negotiation Summary:
Vehicle Damage:
Injury:
Property:
3) Total output must be <= 1500 characters.
4) No markdown, no extra headers, no code blocks.
5) Do NOT invent facts. If unknown/not stated, write "Unknown" or omit.
6) In "Caller:", include relationship ONLY if explicitly stated; otherwise "Unknown relationship".
7) In "Next Steps:", include:
- {company_name}: ...
- Other: ... (or None)

Transcript:
{transcript_text}
"""
