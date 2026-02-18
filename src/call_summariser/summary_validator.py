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


def repair_summary_minimally(summary: str, *, company_name: str) -> str:
    """
    Make *minimal* safe edits so near-miss LLM outputs don't fail validation.
    We never invent call facts; we only add placeholder structure when missing.
    """
    s = summary.strip()

    lines = s.splitlines()

    # --- Ensure Caller header exists ---
    if _line_index(lines, "Caller:") == -1:
        s = "Caller:\nUnknown, Unknown relationship, Inbound\n\n" + s
        lines = s.splitlines()

    # --- Ensure Next Steps exists ---
    if _line_index(lines, "Next Steps:") == -1:
        s += "\n\nNext Steps:\n"
        lines = s.splitlines()

    # --- Normalise Next Steps section ---
    out: list[str] = []
    in_next = False
    found_company = False
    found_other = False

    for line in lines:
        if line.strip() == "Next Steps:":
            in_next = True
            out.append("Next Steps:")
            continue

        if in_next:
            # stop if new section
            if any(line.strip() == h for h in OPTIONAL_HEADER_LINES):
                in_next = False

            stripped = line.strip()

            if stripped.startswith(f"{company_name}:"):
                found_company = True
                out.append(f"- {stripped}")
                continue

            if stripped.startswith("Other:"):
                found_other = True
                out.append(f"- {stripped}")
                continue

        out.append(line)

    # --- Add missing required bullets ---
    if not found_company:
        out.append(f"- {company_name}: None")

    if not found_other:
        out.append("- Other: None")

    return "\n".join(out) + "\n"
