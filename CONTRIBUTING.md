# Contributing to Home Assistant Hermes Conversation Agent

Thanks for taking the time to contribute.

This project is a Home Assistant custom integration that connects to an existing Hermes API endpoint. Contributions should stay focused on the integration itself (`custom_components/hermes_conversation/`) and its tests/docs.

## Before you start

- Read the project overview in [README.md](README.md).
- Read the security policy in [SECURITY.md](SECURITY.md).
- Search existing issues before opening a new one: https://github.com/tilarso/hermes-conversation-agent/issues

## Ways to contribute

- Bug fixes
- Reliability and security improvements
- Tests (unit/behavior coverage)
- Documentation improvements
- Small, focused feature additions that fit the current integration scope

If you plan a larger change, open an issue first to align on scope.

## Development workflow

1. Fork the repository and create a branch from `main`.
2. Make focused changes (code + tests + docs as needed).
3. Run tests locally.
4. Open a pull request with a clear description and validation output.

Example branch naming:

- `fix/config-flow-host-validation`
- `feat/conversation-history-controls`
- `docs/contributing-guide`

## Local setup

```bash
git clone https://github.com/tilarso/hermes-conversation-agent.git
cd hermes-conversation-agent

python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-test.txt 'homeassistant==2026.11.1'
python scripts/install_ha_test_dependencies.py
```

Run tests from repo root:

```bash
python -m pytest -q
python -m ruff check custom_components tests scripts
```

Tests use the real installed Home Assistant framework. The fixtures create an isolated
temporary HA configuration; no running home or real Hermes endpoint is contacted.
Network-boundary tests use a local HTTP server. The platform test loads the real HA
conversation entity, calls its public API, verifies an options-triggered reload, and unloads it.

To test another HA build, install that version and rerun
`python scripts/install_ha_test_dependencies.py` before running the suite. This installs
the conversation dependencies declared by that build instead of copying stale pins.
Use separate virtual environments for each version. Unset an inherited `PYTHONPATH`
when it points to another environment's site-packages.

CI covers HA 2026.11.0, latest stable, and the latest available build including prereleases.
HA 2026.10.4 was also checked: its chat session implementation lacks the user ownership
checks required by this integration's privacy contract, so it is not supported.

## Coding standards

- Follow existing style and keep changes small/targeted.
- Use type hints where practical.
- Preserve current integration behavior unless the PR intentionally changes it.
- Avoid introducing unrelated refactors in the same PR.

For Home Assistant integration code, keep logic explicit and defensive around:

- host/input validation
- API/network error handling
- service payload validation
- multi-entry routing behavior

## Testing expectations

Every code change should include or update tests when behavior changes.

At minimum, contributors should verify:

- config flow behavior (`tests/test_config_flow.py`)
- API client behavior (`tests/test_api.py`)
- conversation behavior (`tests/test_conversation.py`)

If you fix a bug, add a regression test that fails before your fix and passes after it.

## Pull request expectations

Please include in each PR:

- What changed and why
- Any user-visible behavior changes
- Test evidence (command + summary, e.g. `PYTHONPATH=. python -m pytest -q`)
- Linked issue(s), if applicable

For UI/UX or configuration-flow changes, include screenshots/log snippets when helpful.

## Documentation expectations

Update docs when behavior changes:

- [README.md](README.md) for setup/usage/behavior changes
- [SECURITY.md](SECURITY.md) for security-policy changes
- this file for contribution-process changes

## Security reporting

Do not open public issues for vulnerabilities.

Report security issues privately using the process in [SECURITY.md](SECURITY.md), preferably via GitHub Security Advisories:

- https://github.com/tilarso/hermes-conversation-agent/security/advisories

## License

By contributing, you agree your contributions will be licensed under this repository's MIT license.
