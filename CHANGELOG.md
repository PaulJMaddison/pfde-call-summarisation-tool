# Changelog

## 1.0.0 - 2026-08-19

- Reworked transcript parsing to support tab-separated contact-centre exports and bracketed transcripts.
- Added explicit model and company configuration with no stale hard-coded model default.
- Replaced pseudo-timeouts with Gemini SDK HTTP timeouts and bounded transient-error retries.
- Strengthened output validation and summary correction retries.
- Added batch failure isolation, atomic writes, overwrite protection, and input-size limits.
- Added prompt-injection and sensitive-verification-data guidance.
- Added packaging metadata, CI, type checking, coverage, contributor guidance, security policy, and MIT licensing.
