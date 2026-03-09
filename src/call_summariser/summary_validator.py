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

ALLOWED_HEADER_LINES = set(REQUIRED_HEADER_LINES + OPTIONAL_HEADER_LINES)


def _line_index(lines: list[str], target: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == target:
            return i
    return -1


def _find_unknown_headers(lines: list[str]) -> list[str]:
    unknown: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.endswith(":") and stripped and stripped not in ALLOWED_HEADER_LINES:
            unknown.append(stripped)
    return unknown


def _extract_next_steps_lines(lines: list[str]) -> list[str]:
    next_steps_idx = _line_index(lines, "Next Steps:")
    if next_steps_idx == -1:
        return []

    section: list[str] = []
    for line in lines[next_steps_idx + 1 :]:
        stripped = line.strip()
        if stripped in OPTIONAL_HEADER_LINES:
            break
        if stripped:
            section.append(stripped)
    return section


def validate_summary(text: str, *, company_name: str, max_chars: int = 1500) -> None:
    if text.strip().startswith("#"):
        raise ValidationError("Markdown headers are not allowed.")

    if len(text) > max_chars:
        raise ValidationError(f"Summary exceeds {max_chars} characters (got {len(text)}).")

    lines = text.splitlines()

    unknown_headers = _find_unknown_headers(lines)
    if unknown_headers:
        raise ValidationError(f"Unknown header(s) are not allowed: {', '.join(unknown_headers)}")

    indices = []
    for h in REQUIRED_HEADER_LINES:
        idx = _line_index(lines, h)
        if idx == -1:
            raise ValidationError(f"Missing required header line: {h}")
        indices.append(idx)

    if indices != sorted(indices):
        raise ValidationError("Required headers are out of order.")

    next_steps_lines = _extract_next_steps_lines(lines)
    expected_company_prefix = f"- {company_name}:"

    if not any(line.startswith(expected_company_prefix) for line in next_steps_lines):
        raise ValidationError(f"Next Steps must include '{expected_company_prefix}'")

    if not any(line.startswith("- Other:") for line in next_steps_lines):
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

    if _line_index(lines, "Caller:") == -1:
        s = "Caller:\nUnknown, Unknown relationship, Inbound\n\n" + s
        lines = s.splitlines()

    next_steps_idx = _line_index(lines, "Next Steps:")
    if next_steps_idx == -1:
        s += "\n\nNext Steps:\n"
        lines = s.splitlines()
        next_steps_idx = _line_index(lines, "Next Steps:")

    optional_indices = [
        i
        for i, line in enumerate(lines)
        if line.strip() in OPTIONAL_HEADER_LINES and i > next_steps_idx
    ]
    next_steps_end = min(optional_indices) if optional_indices else len(lines)

    before = lines[: next_steps_idx + 1]
    next_steps_body = lines[next_steps_idx + 1 : next_steps_end]
    after = lines[next_steps_end:]

    normalised_next_steps: list[str] = []
    found_company = False
    found_other = False

    for line in next_steps_body:
        stripped = line.strip()
        if not stripped:
            normalised_next_steps.append(line)
            continue

        if stripped.startswith(f"{company_name}:"):
            normalised_next_steps.append(f"- {stripped}")
            found_company = True
            continue

        if stripped.startswith(f"- {company_name}:"):
            found_company = True
            normalised_next_steps.append(line)
            continue

        if stripped.startswith("Other:"):
            normalised_next_steps.append(f"- {stripped}")
            found_other = True
            continue

        if stripped.startswith("- Other:"):
            found_other = True

        normalised_next_steps.append(line)

    if not found_company:
        normalised_next_steps.append(f"- {company_name}: None")

    if not found_other:
        normalised_next_steps.append("- Other: None")

    repaired_lines = before + normalised_next_steps + after
    return "\n".join(repaired_lines).rstrip() + "\n"
