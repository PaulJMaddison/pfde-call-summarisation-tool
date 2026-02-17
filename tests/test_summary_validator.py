import pytest
from call_summariser.summary_validator import ValidationError, validate_summary


def test_requires_exact_required_headers_and_order():
    text = (
        "Subject:\nX\n"
        "Caller:\nY\n"
        "Executive Summary:\nZ\n"
        "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
    )
    with pytest.raises(ValidationError):
        validate_summary(text, company_name="COMPANY_NAME")


def test_rejects_markdown_headers():
    text = (
        "### Caller:\nX\n"
        "Subject:\nY\n"
        "Executive Summary:\nZ\n"
        "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
    )
    with pytest.raises(ValidationError):
        validate_summary(text, company_name="COMPANY_NAME")


def test_enforces_1500_char_limit():
    text = (
        "Caller:\nX\n"
        "Subject:\nY\n"
        "Executive Summary:\n" + ("a" * 2000) + "\n"
        "Next Steps:\n- COMPANY_NAME: A\n- Other: None\n"
    )
    with pytest.raises(ValidationError):
        validate_summary(text, company_name="COMPANY_NAME")


def test_requires_company_next_steps_label_and_other():
    text = (
        "Caller:\nX\n"
        "Subject:\nY\n"
        "Executive Summary:\nZ\n"
        "Next Steps:\n- PFDE: A\n"
    )
    with pytest.raises(ValidationError):
        validate_summary(text, company_name="COMPANY_NAME")
