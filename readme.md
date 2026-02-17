# PFDE Call Summarisation Tool

A Python based command line tool that generates structured insurance
call summaries from raw transcripts using an LLM (Google Gemini), with
strict validation and retry logic to ensure outputs meet required
business constraints.

The tool parses inbound call transcripts and produces summaries that:

-   Follow an exact header structure and ordering
-   Do not exceed 1500 characters
-   Include only relevant optional sections discussed in the call
-   Contain company specific Next Steps
-   Avoid hallucinated or unsupported content

A "golden check" integration script is provided to validate all
generated summaries against these constraints before submission.

------------------------------------------------------------------------

## Project Structure

    src/
      call_summariser/
        cli.py
        gemini_client.py
        optional_gating.py
        prompting.py
        run_result.py
        summariser.py
        summary_validator.py
        transcript_parser.py
    tests/
    tools/
      golden_check.py
    outputs/

------------------------------------------------------------------------

## Setup

### 1. Create and activate virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install project (editable mode)

``` powershell
pip install -e ".[dev]"
```

------------------------------------------------------------------------

## Configure Gemini API Key

Create a `.env` file in the repository root:

    GEMINI_API_KEY=your_api_key_here

This file is ignored via `.gitignore` and must not be committed.

------------------------------------------------------------------------

## Running Unit Tests

``` powershell
python -m pytest
```

All tests are deterministic and use mocked LLM responses.

------------------------------------------------------------------------

## Running the CLI

To generate summaries from transcripts:

``` powershell
python -m call_summariser --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
```

Summaries will be written to the `outputs/` directory.

------------------------------------------------------------------------

## Golden Integration Check

This script runs the full summarisation pipeline on all transcripts and:

-   Validates header structure and order
-   Enforces the 1500 character limit
-   Verifies optional sections are supported by transcript content
-   Ensures Next Steps formatting
-   Retries generation if validation fails
-   Reports any retries used
-   Fails if any summary is invalid

Run:

``` powershell
python tools\golden_check.py --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
```

A successful run will output:

    Golden check PASSED: all transcripts summarised and validated.

------------------------------------------------------------------------

## Constraints Enforced

Generated summaries must:

-   Use exact headers:
    -   Caller:
    -   Subject:
    -   Executive Summary:
    -   Next Steps:
-   Maintain this exact order
-   Be ≤ 1500 characters total
-   Include:
    -   `- COMPANY_NAME:` action
    -   `- Other:` action (or None)
-   Include optional sections only if supported:
    -   Liability Summary:
    -   Negotiation Summary:
    -   Vehicle Damage:
    -   Injury:
    -   Property:
-   Contain no markdown or additional headers
-   Avoid inventing or inferring unknown details

------------------------------------------------------------------------

## Linting

Run Ruff:

``` powershell
ruff check .
```

Auto-fix where possible:

``` powershell
ruff check . --fix
```

------------------------------------------------------------------------

## Pre-Submission Checklist

Before submission:

``` powershell
python -m pytest
ruff check .
python tools\golden_check.py --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
```

All commands should pass without errors.
