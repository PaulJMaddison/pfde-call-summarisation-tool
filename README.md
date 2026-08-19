# Call Summariser

Call Summariser is an open-source Python CLI that turns insurance call transcripts into concise, validated operational summaries using Google Gemini.

It is designed for batch workflows where output shape matters: transcripts are parsed locally, Gemini generates the summary, and deterministic validation rejects malformed output before anything is written.

## Features

- Parses tab-separated contact-centre exports and `[timestamp] SPEAKER: text` transcripts.
- Preserves transcript metadata such as direction and interaction identifiers for model context.
- Treats transcript content as untrusted data to reduce prompt-injection risk.
- Enforces required summary sections, ordering, action lines, and a configurable character limit.
- Retries malformed model output with the previous output and exact validation failure supplied as correction context.
- Uses the Gemini SDK's real HTTP timeout support plus bounded retries for transient failures.
- Processes transcript batches independently so one bad file does not discard successful work.
- Writes summaries atomically to avoid leaving truncated files behind.
- Supports overwrite protection and per-file input-size limits.
- Ships with type checking, linting, coverage, packaging checks, and CI across supported Python versions.

## Requirements

- Python 3.11+
- A Google Gemini API key
- A currently available Gemini text model for your account/project

Model names change over time, so the tool deliberately does not hard-code a model that may later be retired. Configure the model you want to operate explicitly.

## Installation

Clone the repository and install it into a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -e .
```

For development tooling:

```bash
python -m pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and set:

```dotenv
GEMINI_API_KEY=your_api_key
CALL_SUMMARISER_MODEL=your_available_gemini_text_model
CALL_SUMMARISER_COMPANY_NAME=Your Company
```

Environment variables already set by the host process take precedence over `.env` values.

`--model` and `--company-name` can also be supplied directly on the command line and override the corresponding defaults used by the CLI.

## Usage

Process every `.txt` transcript in a directory:

```bash
call-summariser \
  --in-dir transcripts \
  --out-dir outputs \
  --company-name "Acme Insurance" \
  --model "YOUR_GEMINI_MODEL"
```

The same command can be run without installing the console entry point:

```bash
python -m call_summariser --in-dir transcripts --out-dir outputs --company-name "Acme Insurance" --model "YOUR_GEMINI_MODEL"
```

Useful controls:

```text
--max-chars N          Maximum generated summary length (default: 1500)
--summary-attempts N   Attempts to repair structurally invalid model output (default: 3)
--request-attempts N   Attempts for transient Gemini/API failures (default: 4)
--request-timeout S    HTTP request timeout in seconds (default: 30)
--max-input-bytes N    Maximum size of each transcript file (default: 5000000)
--no-overwrite         Keep existing output files and skip them
```

The command returns `0` when all files succeed, `1` when a batch completes with one or more per-file failures, and `2` for configuration or batch-level errors.

## Supported transcript formats

### Tab-separated contact-centre export

```text
Interaction Type:    Call
Interaction ID:      EXAMPLE-001
Direction:           Inbound

Date/Time    Participant Type    Participant    Text
00:01        Internal            Alex Morgan    Good morning, claims team. How can I help?
00:05        External            Jamie Taylor   I am calling for an update on claim CLM-12345.
```

Tabs, rather than spaces, separate the fields in the actual file. See `examples/example-transcript.txt` for a ready-to-copy example.

### Bracketed transcript

```text
Direction: Inbound

[00:01] AGENT: Good morning, claims team. How can I help?
[00:05] CALLER: I am calling for an update on claim CLM-12345.
```

Continuation lines without a new timestamp are appended to the preceding utterance.

## Output contract

Every accepted summary contains these required sections in order:

```text
Caller:
...
Subject:
...
Executive Summary:
...
Next Steps:
- Your Company: ...
- Other: ...
```

The following sections may appear after `Next Steps:` when materially relevant:

```text
Liability Summary:
Negotiation Summary:
Vehicle Damage:
Injury:
Property:
```

Validation ensures that required headers appear exactly once, optional headers are not duplicated, sections are non-empty, no unsupported headers are introduced, `Next Steps` has exactly the two required action lines, and the configured character limit is respected.

Semantic truth still depends on the selected model. The prompt explicitly prohibits invention and the runtime rejects structural failures, but deterministic code cannot prove that every model-generated statement is factually correct. Human or downstream policy review remains appropriate for high-impact decisions.

## Failure handling

API retries and summary-repair retries are deliberately separate:

1. Gemini transport failures such as rate limiting, transient server errors, and timeouts use bounded backoff.
2. A successful model response that violates the summary contract is retried with the exact validation error and previous output.
3. If one transcript still fails, the batch records that failure and continues with the remaining files.
4. A summary is written through a temporary file and atomically replaced only after generation succeeds.

This avoids a network retry being confused with a bad model response and prevents one transcript from invalidating an otherwise successful batch.

## Security and privacy

Transcript text is sent to the configured Gemini service. Before using this tool with real customer data, ensure that your organisation's data-processing, retention, residency, consent, and provider agreements permit that transfer.

The prompt tells the model not to reproduce authentication-only or highly sensitive verification data such as passwords, security answers, full dates of birth, payment-card numbers, or bank details. That is a defence-in-depth measure, not a substitute for upstream redaction or a formal data-loss-prevention policy.

Never commit API keys. `.env` and generated output files are ignored by Git.

For reporting security issues, see `SECURITY.md`.

## Development

Run the quality gate locally:

```bash
ruff check .
mypy
pytest --cov=call_summariser --cov-report=term-missing
python -m build
```

CI runs the same core checks on Python 3.11, 3.12, and 3.13.

## Architecture

```text
text file
   |
   v
transcript_parser.py
   |
   v
prompting.py -> GeminiLLM -> generated text
                         |
                         v
                 summary_validator.py
                         |
                         v
                    atomic output
```

The `Summariser` depends on a small `LLM` protocol rather than the Gemini SDK directly. This keeps generation policy independent from transport and makes alternative providers straightforward to add without rewriting parsing or validation.

## Contributing

Issues and pull requests are welcome. See `CONTRIBUTING.md` for the local quality requirements and contribution workflow.

## Licence

MIT. See `LICENSE`.
