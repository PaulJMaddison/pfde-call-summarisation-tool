# PFDE Call Summarisation Tool

A Python-based command line tool that generates **structured insurance call summaries** from raw transcripts using an LLM (Google Gemini), with **strict validation**, **conditional section gating**, and **retry/repair logic** to ensure outputs meet required business constraints.

The pipeline:

- Parses noisy speech-to-text transcripts
- Builds a structured prompt
- Calls an LLM
- Validates **format/order**, **required sections**, and **≤ 1,500 chars**
- Enforces that optional sections appear **only if supported by transcript content**
- Writes one `*-summary.txt` output per transcript

A **“golden check”** script is provided to run the full pipeline across the 10 evaluation transcripts and fail fast if any output is non-compliant.

---

## Project Structure

```
src/
  call_summariser/
    __main__.py
    cli.py
    gemini_client.py
    golden_check.py
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
pyproject.toml
```

---

## Setup

### 1) Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install (editable mode) + dev dependencies

```bash
pip install -e ".[dev]"
```

---

## Configure Gemini API Key

Create a `.env` file in the repository root:

```dotenv
GEMINI_API_KEY=your_api_key_here
```

- The `.env` file is ignored via `.gitignore` and must not be committed.
- Alternatively you can set `GEMINI_API_KEY` as an environment variable.

---

## Running Unit Tests

```bash
python -m pytest
```

All tests are deterministic and use injected/mocked LLM behaviour (no real Gemini calls).

---

## Running the CLI (Generate Summaries)

To generate summaries from a directory of transcripts:

```bash
python -m call_summariser --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
```

- Summaries are written to `outputs/` as `*-summary.txt`.
- You can override the model with `--model` if desired.

---

## Golden Integration Check (Required Pre-Submission)

This runs the full pipeline over the 10 transcripts and:

- Validates header structure and order
- Enforces the 1,500 character limit
- Verifies optional sections are supported by transcript content
- Ensures `Next Steps` formatting (`- COMPANY_NAME:` and `- Other:`)
- Applies minimal safe repair for common near-miss outputs before validation
- Reports which transcripts required retries
- Fails if any summary is invalid or if not all 10 outputs are written

### Run (recommended command)

This command explicitly invokes the **refactored** golden check in `src/call_summariser/golden_check.py`:

```bash
python -c "from call_summariser.golden_check import main; import sys; raise SystemExit(main(sys.argv[1:]))" --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
```

(You may still have `tools/golden_check.py`, but the command above guarantees you are using the up-to-date golden check implementation in `src/`.)

A successful run prints:

```
Golden check PASSED: all transcripts summarised and validated.
```

---

## Constraints Enforced

Generated summaries must:

- Use exact required headers as whole lines, in this order:
  - `Caller:`
  - `Subject:`
  - `Executive Summary:`
  - `Next Steps:`
- Be **≤ 1500 characters** total
- Include **both** Next Steps lines:
  - `- COMPANY_NAME: ...`
  - `- Other: ...` (or `None`)
- Include optional sections **only if supported by the transcript**:
  - `Liability Summary:`
  - `Negotiation Summary:`
  - `Vehicle Damage:`
  - `Injury:`
  - `Property:`
- Contain no markdown and no extra headers
- Avoid inventing unknown details (use `Unknown` where appropriate)

---

## Linting

Run Ruff:

```bash
ruff check .
```

Auto-fix where possible:

```bash
ruff check . --fix
```

---

## Pre-Submission Checklist

```bash
python -m pytest
ruff check .
python -c "from call_summariser.golden_check import main; import sys; raise SystemExit(main(sys.argv[1:]))" --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
```

All commands should pass without errors, and `outputs/` should contain 10 `*-summary.txt` files.

---

## Evaluation Criteria Used to Assess Solution Quality

During development, each generated summary was assessed against the five specified quality checks:

1. **Issue Identification & Actions Taken**
   - Summary clearly captures why the call happened and what was done.

2. **Accuracy of Critical Facts**
   - Prompt instructs no invention.
   - Optional sections are gated against the transcript to reduce hallucination risk.
   - Unknowns are recorded as `Unknown`.

3. **Operational Handover Readiness**
   - Mandatory `Next Steps` always includes both company and other-party actions.

4. **Professional Tone**
   - Prompt prohibits markdown and informal content; outputs are suitable for customer visibility.

5. **Character Limit Compliance (≤ 1,500)**
   - Automated validation rejects oversize outputs; retry path requests more concise rewrites.

These checks are enforced programmatically in `summary_validator.py` and `optional_gating.py` to reduce format drift and unsupported content.

---

## Trade-off Analysis for Key Decisions

- **Strict validation vs throughput**
  - Exact headers/order improves downstream reliability.
  - Can increase retries under free-tier quotas.
  - Mitigated with minimal local repair for near-miss outputs.

- **Retry attempts**
  - `max_attempts` is capped to prevent infinite loops and control cost/quota usage.
  - Golden check uses a conservative attempt count to reduce quota burn.

- **Prompt engineering vs post-processing**
  - Prompt drives most correctness.
  - Lightweight repair is used to fix structural near-misses without inventing facts.

- **Raw API calls vs framework**
  - Direct SDK usage keeps dependencies minimal and behaviour explicit.
  - Layering keeps the LLM boundary mockable for tests.

---

## Production Deployment Considerations

- **Rate limiting & backoff**
  - Implement exponential backoff for 429/503.
  - Use queue-based processing to avoid burst limits.

- **Observability**
  - Log attempts per transcript, validation failures, and gating outcomes.

- **Configuration**
  - Externalise model name, company name, max attempts, and char limits.

- **Security**
  - API keys via env vars / `.env`, excluded from Git.

- **Scalability**
  - Parallelise transcript processing via workers, cache successful outputs, and avoid reprocessing.

---

## Demonstration of Edge Case Handling

The system explicitly handles:

- **Missing/malformed required headers**
  - Validation fails with clear error messages.

- **Unsupported optional sections**
  - Optional sections are validated against transcript content (reduces hallucinated sections).

- **Unknown caller relationship/direction**
  - Prompt and repair logic use safe placeholders rather than inventing facts.

- **Transcript noise (STT artefacts)**
  - Parser tolerates fragmented lines and encoding artefacts.

- **Partial output writes**
  - Golden check fails if fewer than 10 outputs are written.

- **Character limit exceeded**
  - Validation rejects oversize outputs; retry path asks the model to rewrite concisely.

---
