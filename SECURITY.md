# Security Policy

## Reporting a vulnerability

Please do not publish credentials, private keys, personal data, or exploitable vulnerability details in public issues.

Use GitHub's private vulnerability reporting feature for this repository if it is enabled. Otherwise, contact the repository owner through the GitHub profile and request a private reporting channel.

## Secret-handling rules

- Never commit signing keystores, passwords, access tokens, API keys, or local environment files.
- Store release-signing material only in GitHub Actions Secrets.
- Never include a keystore or private key in workflow artifacts, logs, releases, or APKs.
- Treat all workflow logs and artifacts from this public repository as publicly accessible.
- Rotate any credential that has appeared in repository history or a public artifact.
