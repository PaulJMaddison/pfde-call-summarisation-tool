from __future__ import annotations

import re
from call_summariser.summary_validator import OPTIONAL_HEADER_LINES, ValidationError


_KEYWORDS = {
    "Liability Summary:": ["fault", "liable", "liability", "responsible", "blame"],
    "Negotiation Summary:": ["offer", "settlement", "negot", "counter"],
    "Vehicle Damage:": ["damage", "repair", "garage", "towed", "tow", "hire car", "rental"],
    "Injury:": ["injury", "injured", "pain", "hospital", "gp", "treatment", "physio"],
    "Property:": ["property", "fence", "wall", "gate", "lamppost"],
}


def validate_optional_sections_against_transcript(summary: str, transcript_text: str) -> None:
    transcript_lc = transcript_text.lower()
    present = [h for h in OPTIONAL_HEADER_LINES if f"\n{h}\n" in f"\n{summary}"]

    for h in present:
        kws = _KEYWORDS.get(h, [])
        if kws and not any(re.search(rf"\b{re.escape(k)}", transcript_lc) for k in kws):
            raise ValidationError(
                f"Optional section '{h}' present but transcript does not support it."
            )
