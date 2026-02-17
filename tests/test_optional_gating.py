import pytest
from call_summariser.optional_gating import validate_optional_sections_against_transcript
from call_summariser.summary_validator import ValidationError


def test_rejects_injury_section_when_transcript_has_no_injury_keywords():
    transcript = "Caller discussed repairs only."
    summary = (
        "Caller:\nX\n"
        "Subject:\nY\n"
        "Executive Summary:\nZ\n"
        "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
        "Injury:\nNone\n"
    )
    with pytest.raises(ValidationError):
        validate_optional_sections_against_transcript(summary, transcript)


def test_allows_vehicle_damage_when_transcript_mentions_tow_or_repair():
    transcript = "Vehicle was towed and repair arranged."
    summary = (
        "Caller:\nX\n"
        "Subject:\nY\n"
        "Executive Summary:\nZ\n"
        "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
        "Vehicle Damage:\nTow arranged\n"
    )
    validate_optional_sections_against_transcript(summary, transcript)
