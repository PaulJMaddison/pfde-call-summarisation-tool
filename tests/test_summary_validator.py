import pytest

from call_summariser.errors import SummaryValidationError
from call_summariser.summary_validator import validate_summary

COMPANY = "Acme Insurance"


def valid_summary() -> str:
    return (
        "Caller:\nDavid, policyholder\n"
        "Subject:\nClaim status\n"
        "Executive Summary:\nCaller requested an update.\n"
        "Next Steps:\n"
        "- Acme Insurance: Assessor to contact caller.\n"
        "- Other: None\n"
        "Property:\nKitchen water damage reported.\n"
    )


def test_accepts_valid_summary():
    validate_summary(valid_summary(), company_name=COMPANY)


def test_rejects_duplicate_required_header():
    text = valid_summary().replace("Subject:\n", "Subject:\nSubject:\n", 1)
    with pytest.raises(SummaryValidationError, match="exactly once"):
        validate_summary(text, company_name=COMPANY)


def test_rejects_optional_section_before_next_steps():
    text = valid_summary().replace("Property:\nKitchen water damage reported.\n", "")
    text = text.replace(
        "Executive Summary:\nCaller requested an update.\n",
        "Executive Summary:\nCaller requested an update.\nProperty:\nDamage.\n",
    )
    with pytest.raises(SummaryValidationError, match="after 'Next Steps:'"):
        validate_summary(text, company_name=COMPANY)


def test_rejects_unknown_header():
    text = valid_summary() + "Extra Section:\nNope\n"
    with pytest.raises(SummaryValidationError, match="Unknown header"):
        validate_summary(text, company_name=COMPANY)


def test_rejects_empty_required_section():
    text = valid_summary().replace("Subject:\nClaim status\n", "Subject:\n")
    with pytest.raises(SummaryValidationError, match="Subject"):
        validate_summary(text, company_name=COMPANY)


def test_rejects_wrong_or_duplicate_next_step_actions():
    text = valid_summary().replace(
        "- Other: None\n",
        "- Other: None\n- Third Party: Call back.\n",
    )
    with pytest.raises(SummaryValidationError, match="unsupported action"):
        validate_summary(text, company_name=COMPANY)


def test_rejects_character_limit():
    with pytest.raises(SummaryValidationError, match="exceeds"):
        validate_summary(valid_summary() + ("x" * 1600), company_name=COMPANY)


def test_rejects_markup_order_duplicate_optional_and_empty_optional():
    with pytest.raises(SummaryValidationError, match="Code fences"):
        validate_summary(valid_summary() + "```", company_name=COMPANY)
    with pytest.raises(SummaryValidationError, match="Markdown"):
        validate_summary("# heading\n" + valid_summary(), company_name=COMPANY)

    out_of_order = valid_summary().replace(
        "Subject:\nClaim status\nExecutive Summary:\nCaller requested an update.\n",
        "Executive Summary:\nCaller requested an update.\nSubject:\nClaim status\n",
    )
    with pytest.raises(SummaryValidationError, match="out of order"):
        validate_summary(out_of_order, company_name=COMPANY)

    duplicate_optional = valid_summary() + "Property:\nAgain\n"
    with pytest.raises(SummaryValidationError, match="more than once"):
        validate_summary(duplicate_optional, company_name=COMPANY)

    empty_optional = valid_summary().replace(
        "Property:\nKitchen water damage reported.\n",
        "Property:\n",
    )
    with pytest.raises(SummaryValidationError, match="Optional section"):
        validate_summary(empty_optional, company_name=COMPANY)


def test_rejects_missing_next_step_party_lines():
    missing_company = valid_summary().replace(
        "- Acme Insurance: Assessor to contact caller.\n", ""
    )
    with pytest.raises(SummaryValidationError, match="Acme Insurance"):
        validate_summary(missing_company, company_name=COMPANY)

    missing_other = valid_summary().replace("- Other: None\n", "")
    with pytest.raises(SummaryValidationError, match="Other"):
        validate_summary(missing_other, company_name=COMPANY)
