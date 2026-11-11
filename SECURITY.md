# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| latest  | ✅ |

Only the latest release on the `main` branch receives security updates. If you are running an older version, please upgrade before reporting.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a vulnerability privately, use one of the following channels:

1. **GitHub Security Advisories (preferred):** Open [Security -> Advisories](../../security/advisories) in this repository and click **Report a vulnerability**.
2. **Email:** Contact the repository owner via the email listed on their GitHub profile.

### What to include

- A clear description of the vulnerability and its potential impact.
- Steps to reproduce, including configuration details and versions.
- Any proof-of-concept code or logs (sanitize credentials before sharing).

### What to expect

- **Acknowledgement** within **72 hours**.
- **Initial assessment** (confirmed / needs-more-info / not-applicable) within **7 days**.
- **Fix or mitigation** for confirmed vulnerabilities within **30 days**, depending on severity and complexity.
- A coordinated disclosure timeline agreed upon with the reporter before any public announcement.

## Scope

In scope:

- The Home Assistant custom integration code under `custom_components/hermes_conversation/`.
- Configuration flow, API client logic, and conversation handlers.
- Credentials/tokens handled by the integration.
- Dependencies declared in `manifest.json`.

Out of scope:

- Hermes server vulnerabilities outside this integration repository.
- Home Assistant core vulnerabilities (report those to Home Assistant Security).
- Issues in third-party HACS infrastructure.

## Coordinated Disclosure

We follow coordinated disclosure practices:

1. Reporter and maintainers agree on a disclosure timeline (typically 90 days from confirmation).
2. A fix is developed and tested privately.
3. A new release is published with the fix, and a security advisory is created.
4. Reporter is credited in the advisory unless they prefer anonymity.

## Security Design Principles

- **Configurable transport security:** Use an `https://` backend URL for TLS.
  `verify_ssl` controls certificate verification and defaults to true; it does not
  add encryption to an `http://` URL. Disabling verification permits interception.
- **No credential logging:** API keys and secrets must never be logged.
- **Input validation:** User-supplied values are validated to reduce unsafe targets and malformed requests.
- **Least privilege:** The integration requests only the Home Assistant functionality needed for operation.

## Credentials, history, and endpoint trust

- API keys use Home Assistant's standard config-entry storage. This integration
  adds no encryption at rest. Protect HA's configuration directory and backups.
- Configure only a backend you trust. Local network hosts are intentionally allowed;
  URL syntax validation is not an SSRF sandbox or a network access-control policy.
- Embedded URL credentials, query parameters, fragments, and redirects are rejected.
- The integration never logs raw HTTP response bodies, even at debug level.
  HA's own conversation debug logging may include messages; treat diagnostic logs as private.
- HA manages chat-session ownership and expiration. Outbound text history is bounded
  by `max_history`; the integration does not keep a second history cache. This does not
  control history retained by the Hermes backend.
- Successful JSON responses are limited to 1 MiB of decompressed bytes, including
  responses without a Content-Length header. Error bodies are not read or logged.
- Chat POSTs are not retried automatically: an error does not prove that no action occurred.
