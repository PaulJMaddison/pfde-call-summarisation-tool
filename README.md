# Call Summariser

Call Summariser is a free, open-source tool that turns insurance call transcripts into short, useful summaries using Google Gemini.

Give it a folder containing call transcripts and it will create a summary file for each call.

It is designed to save someone from reading a full transcript just to understand:

- who called
- what the call was about
- what happened
- what needs to happen next
- important details about liability, damage, injury, property or negotiations when they were discussed

The tool checks every summary before saving it. If Gemini returns the wrong format, the tool asks it to correct the answer. If one transcript fails, the other transcripts can still be processed.

## What you need

- Python 3.11 or newer
- a Google Gemini API key
- the name of a Gemini model you can use

## Quick start

### 1. Download the project

Clone this repository and open a terminal in the project folder.

### 2. Create a Python environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install Call Summariser

```bash
python -m pip install -e .
```

### 4. Add your Gemini settings

Copy `.env.example` to a new file called `.env`.

Add your own values:

```dotenv
GEMINI_API_KEY=your_api_key
CALL_SUMMARISER_MODEL=your_gemini_model
CALL_SUMMARISER_COMPANY_NAME=Your Company
```

Do not commit your `.env` file or API key to GitHub.

### 5. Add some transcripts

Create a folder called `transcripts` and put your `.txt` transcript files inside it.

There is a simple example in:

```text
examples/example-transcript.txt
```

### 6. Create the summaries

```bash
call-summariser --in-dir transcripts --out-dir outputs
```

The summaries will be written to the `outputs` folder.

You can also run the tool like this:

```bash
python -m call_summariser --in-dir transcripts --out-dir outputs
```

## Example

If your input folder contains:

```text
transcripts/
  call-001.txt
  call-002.txt
  call-003.txt
```

Call Summariser will create files such as:

```text
outputs/
  call-001-summary.txt
  call-002-summary.txt
  call-003-summary.txt
```

A summary looks like this:

```text
Caller:
Jamie Taylor, Unknown relationship, Inbound

Subject:
Update on claim CLM-12345

Executive Summary:
Jamie called for an update on an existing claim. The claim is currently being reviewed and the caller was told when to expect the next update.

Next Steps:
- Acme Insurance: Contact Jamie when the review is complete.
- Other: None
```

If they are relevant to the call, the summary can also include sections for:

- liability
- negotiations
- vehicle damage
- injury
- property damage

## Transcript formats

Call Summariser understands two common text formats.

### Contact-centre export

The first format uses columns separated by tabs:

```text
Interaction Type:    Call
Interaction ID:      EXAMPLE-001
Direction:           Inbound

Date/Time    Participant Type    Participant    Text
00:01        Internal            Alex Morgan    Good morning, claims team. How can I help?
00:05        External            Jamie Taylor   I am calling for an update on claim CLM-12345.
```

The example above is shown with spaces for readability. In the real file, the columns should be separated by tabs.

### Simple timestamp format

It also understands transcripts like this:

```text
Direction: Inbound

[00:01] AGENT: Good morning, claims team. How can I help?
[00:05] CALLER: I am calling for an update on claim CLM-12345.
```

If a sentence continues onto the next line without a new timestamp, it is added to the previous line of dialogue.

## Changing the company or model

You can keep the company name and Gemini model in your `.env` file, or provide them when you run the command:

```bash
call-summariser \
  --in-dir transcripts \
  --out-dir outputs \
  --company-name "Acme Insurance" \
  --model "YOUR_GEMINI_MODEL"
```

Command-line values take priority over the values in `.env`.

## Other useful options

You normally do not need to change these, but they are available when needed:

```text
--max-chars N          Maximum length of a summary. Default: 1500 characters.
--summary-attempts N   How many times Gemini can correct a badly formatted summary. Default: 3.
--request-attempts N   How many times to retry a temporary Gemini/API error. Default: 4.
--request-timeout S    How long to wait for a Gemini request. Default: 30 seconds.
--max-input-bytes N    Maximum size of one transcript file. Default: 5 MB.
--no-overwrite         Do not replace a summary file that already exists.
```

Run this to see all options:

```bash
call-summariser --help
```

## What happens when something goes wrong?

The tool is designed so that one problem does not ruin the whole batch.

- If Gemini has a temporary error, the request is tried again.
- If Gemini returns a summary in the wrong format, it is asked to correct it.
- If one transcript still cannot be summarised, the tool reports that file and moves on to the others.
- A summary is only saved after it has been completed successfully, so you should not be left with half-written files.

The command returns:

- `0` when every transcript succeeds
- `1` when some transcripts succeed and others fail
- `2` when the command itself cannot start correctly, for example because settings are missing

## What the tool checks

Before a summary is saved, Call Summariser checks that it:

- contains the required sections
- puts those sections in the right order
- contains exactly the two required next-step action lines and no extra content in that section
- does not contain duplicate or unexpected sections
- is not longer than the allowed limit, including summaries exactly at the configured maximum length

Gemini is also told not to invent information that is not in the transcript.

No AI system can guarantee that every generated sentence is factually correct. If the summary will be used to make an important decision, it should still be reviewed by a person or another suitable checking process.

## Privacy and customer data

Transcript text is sent to the Google Gemini service you configure.

Before using real customer calls, make sure your organisation allows that data to be sent to Gemini and that your privacy, data retention and data location requirements are covered.

The tool tells Gemini not to repeat highly sensitive information such as:

- passwords
- security answers
- full dates of birth used for identity checks
- payment card numbers
- bank details

You should still remove sensitive information before sending transcripts if your organisation requires it.

Never commit API keys, real customer transcripts or generated customer summaries to a public repository.

See `SECURITY.md` for information about reporting security problems.

## How it works

At a high level the process is simple:

```text
Transcript file
      |
      v
Read and understand the transcript
      |
      v
Send it to Gemini with summary instructions
      |
      v
Check the answer
      |
      v
Save the summary
```

The code keeps the Gemini connection separate from the rest of the summarising logic. This makes it easier to support another AI provider in the future without rewriting the whole tool.

## For developers

Install the development tools with:

```bash
python -m pip install -e ".[dev]"
```

Run the local checks with:

```bash
ruff check .
mypy
pytest --cov=call_summariser --cov-report=term-missing
python -m build
```

Latest local verification on the current implementation:

- package build passed
- 44 unit tests passed
- 0 unit tests failed
- 90.79% branch-aware test coverage

The unit tests use mocks and fakes for Gemini, so they do not call the real Gemini API or require Docker, databases, browsers, cloud services or other local infrastructure.

The project does not use GitHub Actions. These checks are run locally, so using or contributing to the repository does not require paid GitHub Actions minutes.

## Contributing

Contributions are welcome.

See `CONTRIBUTING.md` for the contribution guide.

## Licence

Call Summariser is released under the MIT Licence. See `LICENSE`.
