from __future__ import annotations

from call_summariser.errors import SummaryValidationError
from call_summariser.prompting import OPTIONAL_HEADERS, REQUIRED_HEADERS

ALLOWED_HEADERS = frozenset((*REQUIRED_HEADERS, *OPTIONAL_HEADERS))


def _indices(lines: list[str], header: str) -> list[int]:
    return [index for index, line in enumerate(lines) if line.strip() == header]


def _section_body(lines: list[str], header_index: int) -> list[str]:
    body: list[str] = []
    for line in lines[header_index + 1 :]:
        stripped = line.strip()
        if stripped in ALLOWED_HEADERS:
            break
        if stripped:
            body.append(stripped)
    return body


def validate_summary(text: str, *, company_name: str, max_chars: int = 1500) -> None:
    if not isinstance(text, str) or not text.strip():
        raise SummaryValidationError("Summary is empty.")
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")
    if len(text) > max_chars:
        raise SummaryValidationError(
            f"Summary exceeds {max_chars} characters (got {len(text)})."
        )
    if "```" in text:
        raise SummaryValidationError("Code fences are not allowed.")

    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            raise SummaryValidationError("Markdown headings are not allowed.")
        if (
            stripped.endswith(":")
            and not stripped.startswith("-")
            and stripped not in ALLOWED_HEADERS
        ):
            raise SummaryValidationError(f"Unknown header is not allowed: {stripped}")

    required_positions: list[int] = []
    for header in REQUIRED_HEADERS:
        positions = _indices(lines, header)
        if len(positions) != 1:
            raise SummaryValidationError(
                f"Required header '{header}' must appear exactly once."
            )
        required_positions.append(positions[0])

    if required_positions != sorted(required_positions):
        raise SummaryValidationError("Required headers are out of order.")

    for header in OPTIONAL_HEADERS:
        positions = _indices(lines, header)
        if len(positions) > 1:
            raise SummaryValidationError(f"Optional header '{header}' appears more than once.")
        if positions and positions[0] < required_positions[-1]:
            raise SummaryValidationError(
                f"Optional header '{header}' must appear after 'Next Steps:'."
            )

    for header, position in zip(REQUIRED_HEADERS, required_positions, strict=True):
        if not _section_body(lines, position):
            raise SummaryValidationError(f"Required section '{header}' is empty.")

    for header in OPTIONAL_HEADERS:
        positions = _indices(lines, header)
        if positions and not _section_body(lines, positions[0]):
            raise SummaryValidationError(f"Optional section '{header}' is empty.")

    next_steps = _section_body(lines, required_positions[-1])
    company_prefix = f"- {company_name}:"
    company_lines = [line for line in next_steps if line.startswith(company_prefix)]
    other_lines = [line for line in next_steps if line.startswith("- Other:")]
    if len(company_lines) != 1:
        raise SummaryValidationError(
            f"Next Steps must contain exactly one '{company_prefix}' action line."
        )
    if len(other_lines) != 1:
        raise SummaryValidationError(
            "Next Steps must contain exactly one '- Other:' action line."
        )

    unexpected_lines = [
        line for line in next_steps if line not in (*company_lines, *other_lines)
    ]
    if unexpected_lines:
        raise SummaryValidationError(
            "Next Steps contains an unsupported action line or extra content."
        )
