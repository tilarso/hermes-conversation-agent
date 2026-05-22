# Home Assistant Hermes Conversation Agent

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Contributing](https://img.shields.io/badge/Contributing-Guide-blue.svg)](./CONTRIBUTING.md)
[![Security](https://img.shields.io/badge/Security-Policy-red.svg)](./SECURITY.md)


[![Add to Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tilarso&repository=hermes-conversation-agent&category=integration)

Hermes Conversation Agent is a Home Assistant custom integration that registers a conversation agent and forwards user utterances to a Hermes gateway using an OpenAI-compatible chat completions endpoint.

## Features

- Home Assistant config flow (`host`, optional `api_key`, `verify_ssl`)
- Conversation agent entity selectable in Voice Assistants
- Preserves conversation continuity via `conversation_id`
- Options flow for `model`, `system_prompt`, `timeout`, and `max_history`
- Safe handling for auth errors, timeouts, and transient gateway failures

## What this project is (and is not)

This repository contains a Home Assistant integration (`custom_components/hermes_conversation`) that talks to an existing Hermes API endpoint.

It does not install Hermes itself. You must run Hermes separately, then point Home Assistant to that server.

## Prerequisites

- Home Assistant with HACS installed
- A reachable Hermes gateway/API endpoint
- Hermes host URL
- Optional API key if your Hermes deployment requires auth

## Installation

### Option A: HACS (recommended)

1. Open HACS -> Integrations.
2. Open the menu (3 dots) -> Custom repositories.
3. Add repository URL:
   - `https://github.com/tilarso/hermes-conversation-agent`
   - Category: `Integration`
4. Search for `Hermes Conversation Agent` in HACS and install it.
5. Restart Home Assistant.

You can also use the "Add to Home Assistant" button above to add the custom repository.

### Option B: Manual install

1. Copy `custom_components/hermes_conversation` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to Settings -> Devices & Services.
2. Click Add Integration.
3. Search for `Hermes Conversation Agent`.
4. Enter:
   - `Hermes URL` (example: `http://192.168.1.74:8765`)
   - `API key` (optional)
   - `Verify SSL` (disable only for self-signed/internal TLS setups)
5. Submit and select `Hermes` in Voice Assistants.

## Runtime behavior

- The integration posts to `<host>/v1/chat/completions` with `stream=false`.
- Health validation checks `<host>/api/health` then `<host>/health`.
- For MVP, thread continuity maps Home Assistant `conversation_id` to Hermes `thread_id`.

## Security

See [SECURITY.md](./SECURITY.md).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT. See [LICENSE](./LICENSE).
