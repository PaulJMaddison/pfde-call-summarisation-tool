from __future__ import annotations


class ValidationError(ValueError):
    pass


REQUIRED_HEADER_LINES = [
    "Caller:",
    "Subject:",
    "Executive Summary:",
    "Next Steps:",
]

OPTIONAL_HEADER_LINES = [
    "Liability Summary:",
    "Negotiation Summary:",
    "Vehicle Damage:",
    "Injury:",
    "Property:",
]


def _line_index(lines: list[str], target: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == target:
            return i
    return -1


def validate_summary(text: str, *, company_name: str, max_chars: int = 1500) -> None:
    if text.strip().startswith("#"):
        raise ValidationError("Markdown headers are not allowed.")

    if len(text) > max_chars:
        raise ValidationError(f"Summary exceeds {max_chars} characters (got {len(text)}).")

    lines = text.splitlines()

    indices = []
    for h in REQUIRED_HEADER_LINES:
        idx = _line_index(lines, h)
        if idx == -1:
            raise ValidationError(f"Missing required header line: {h}")
        indices.append(idx)

    if indices != sorted(indices):
        raise ValidationError("Required headers are out of order.")

    expected_company = f"- {company_name}:"
    if expected_company not in text:
        raise ValidationError(f"Next Steps must include '{expected_company}'")
    if "- Other:" not in text:
        raise ValidationError("Next Steps must include '- Other:'")

    for h in OPTIONAL_HEADER_LINES:
        if h in text and _line_index(lines, h) == -1:
            raise ValidationError(f"Optional header '{h}' must appear as its own line.")
