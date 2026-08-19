# Security Policy

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose customer data, credentials, or third-party service access.

Use GitHub's private vulnerability reporting feature for this repository when available. Include the affected version or commit, reproduction details, impact, and any suggested mitigation.

## Secrets and customer data

Do not commit Gemini API keys, `.env` files, real customer transcripts, generated customer summaries, authentication answers, payment data, or other sensitive production material.

This project sends transcript content to the configured Gemini service. Operators are responsible for confirming that their provider configuration and organisational policies are appropriate for the data being processed.
