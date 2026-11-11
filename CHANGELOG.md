# Changelog

## v0.2.0 — Home Assistant compatibility and privacy hardening

### Upgrade requirements

- Requires Home Assistant 2026.11.0 or newer. Tested with HA 2026.11.0 and 2026.11.1.
- The integration no longer advertises native Home Assistant device control: it forwards text to Hermes and does not expose HA's LLM tools. Tools provided independently by the Hermes backend are unaffected.
- Configure the final HTTP(S) backend URL directly. Redirects, embedded credentials, query parameters, and fragments are rejected.
- After updating the integration, restart Home Assistant to load the new code. Later options changes reload only this integration.

### Fixed

- Use Home Assistant's native ChatLog hook for session IDs, conversation history, user ownership checks, concurrent-turn protection, and expiration.
- Apply saved model, system prompt, timeout, and history options through automatic entry reload.
- Return proper error results instead of reporting backend failures as successful actions.
- Preserve authentication, timeout, and server failures during health validation. Fall back between health endpoints only on missing/unsupported endpoints.
- Never automatically replay chat POSTs, which could otherwise repeat an action already executed by the backend.
- Disable HTTP redirects to prevent forwarding conversation payloads to unintended endpoints.
- Safely parse malformed Retry-After headers and unexpected response shapes.
- Limit consumed JSON response bodies to 1 MiB after decompression, including chunked responses. Remove raw upstream error-body logging.
- Remove the custom history-cache eviction race.
- Correct the CI condition that silently skipped HACS validation.

### Verification and maintenance

- Replace Home Assistant stubs with real-framework tests, including platform setup, public conversation processing, options reload, and unload.
- 47 tests pass on each tested HA version; lint and workflow syntax checks also pass locally.
- Add scheduled CI coverage for the minimum supported version, latest stable, and newest available build including prereleases.
- Update pinned GitHub Actions and clarify TLS, credential storage, history retention, and endpoint trust documentation.

### Known scope

- Responses remain non-streaming text; native HA tool calling is not implemented.
- No running Home Assistant installation is modified by publishing this release. A live Assist/STT/TTS smoke test against the intended Hermes backend has not been performed.
- Home Assistant's own debug logs and the Hermes backend can retain conversation data independently of this integration. Protect diagnostics, configuration files, and backups.
