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

## Evaluation Criteria Used to Assess Solution Quality

During development, each generated summary was evaluated against the
five specified quality checks:

1.  **Issue Identification & Actions Taken**
    -   Ensured the summary clearly captured the purpose of the call and
        the actions agreed.
    -   Verified that another agent could continue the case using the
        summary alone.
2.  **Accuracy of Critical Facts**
    -   Prompt instructed the LLM not to invent information.
    -   Validation step enforced structural correctness; unknowns were
        recorded as "Unknown".
3.  **Operational Handover Readiness**
    -   Mandatory `Next Steps` section always includes:
        -   `- COMPANY_NAME:`
        -   `- Other:`
    -   Ensures downstream agents know responsibilities.
4.  **Professional Tone**
    -   Prompt prohibits markdown and informal language.
    -   Encourages concise, customer-appropriate phrasing.
5.  **Character Limit Compliance (≤ 1500)**
    -   Automated validation rejects outputs exceeding limits.
    -   Retry mechanism prompts LLM to rewrite concisely when required.

Automated checks in `summary_validator.py` map directly to these
criteria to reduce hallucinations and formatting errors.

------------------------------------------------------------------------

## Trade-off Analysis for Key Decisions

-   **Strict Validation vs. Throughput**
    -   Enforcing exact headers and section order improves downstream
        reliability.
    -   May increase retries under free-tier LLM quotas.
    -   Mitigated via minimal local repair for near-miss outputs.
-   **Retry Attempts**
    -   `max_attempts=1` balances quality improvement with API cost.
    -   Prevents infinite loops on non-compliant outputs.
-   **Prompt Engineering vs. Post-Processing**
    -   Primary behaviour driven by prompt to minimise hallucination.
    -   Lightweight post-validation/repair avoids additional LLM calls.
-   **Model Choice (Gemini Flash)**
    -   Selected for low latency and cost efficiency.
    -   Free-tier quotas require batch runs; system supports
        accumulation of outputs across runs.

------------------------------------------------------------------------

## Production Deployment Considerations

-   **Rate Limiting & Backoff**
    -   Implement exponential backoff for 429/503 responses.
    -   Queue transcripts to avoid burst limits.
-   **Observability**
    -   Log:
        -   attempts used per transcript
        -   validation failures
        -   optional section gating outcomes
-   **Configuration**
    -   Externalise:
        -   model name
        -   company name
        -   max attempts
        -   character limits
-   **Security**
    -   Store API keys via environment variables (`.env`).
    -   Exclude secrets via `.gitignore`.
-   **Scalability**
    -   Process transcripts asynchronously in a worker queue.
    -   Cache successful summaries to avoid reprocessing.

------------------------------------------------------------------------

## Demonstration of Edge Case Handling

The system explicitly handles:

-   **Missing or malformed headers**
    -   Validation rejects non-compliant structure.
-   **Hallucinated optional sections**
    -   `optional_gating.py` ensures sections appear only if discussed
        in transcript.
-   **Unknown Caller Relationship/Direction**
    -   Prompt instructs use of "Unknown" when not explicitly stated.
-   **Transcript Noise (STT Artifacts)**
    -   Parser tolerates encoding artefacts and fragmented sentences.
-   **Partial Output Writes**
    -   Golden check fails if fewer than 10 summaries are written.
-   **Character Limit Exceeded**
    -   Output rejected and retried with concision instruction.

These checks improve robustness for real-world speech-to-text transcript
quality issues.

