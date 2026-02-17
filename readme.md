# .env (DO NOT COMMIT)
GEMINI_API_KEY=YOUR_KEY

# Run unit tests
python -m pytest

# Generate summaries
python -m call_summariser --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME

# Golden check (validates + reports retries + fails on any invalid)
python tools/golden_check.py --in-dir "Transcripts to Summarise" --out-dir outputs --company-name COMPANY_NAME
