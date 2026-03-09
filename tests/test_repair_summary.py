from call_summariser.summary_validator import repair_summary_minimally


def test_repair_adds_missing_next_steps_bullets_within_next_steps_section() -> None:
    raw = (
        "Caller:\nX\n"
        "Subject:\nY\n"
        "Executive Summary:\nZ\n"
        "Next Steps:\n"
        "Liability Summary:\nUnknown\n"
    )

    repaired = repair_summary_minimally(raw, company_name="COMPANY_NAME")

    next_steps_block = repaired.split("Next Steps:\n", 1)[1].split("Liability Summary:", 1)[0]
    assert "- COMPANY_NAME: None" in next_steps_block
    assert "- Other: None" in next_steps_block
