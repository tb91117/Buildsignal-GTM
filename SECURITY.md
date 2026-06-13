# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Email the maintainer with details and a
reproduction; you'll get an acknowledgment within a few days.

## How this project handles secrets

- **Bring-your-own-key.** No credential is ever committed. All keys load from `.env` (gitignored) via
  `pydantic-settings`. `.env.example` documents the variables with placeholders only.
- **`detect-private-key`** runs as a pre-commit hook to block accidental key commits.
- **Webhook authenticity.** Inbound webhooks are verified with an HMAC-SHA256 signature
  (`WEBHOOK_SIGNING_SECRET`) using a constant-time comparison.
- **Least privilege.** The Docker image runs as a non-root user.

## Handling lead data (PII)

Inbound leads are personal data. When self-hosting:

- Restrict the `/leads` endpoint (network policy / API gateway) and always set a signing secret.
- Treat your CRM/Slack destinations as the system of record; this service is stateless by default.
- If you enable auto-send, ensure your outbound email complies with CAN-SPAM / GDPR
  (identification + unsubscribe). See [`docs/compliance.md`](docs/compliance.md).
