# Hermes Conversation Agent (Home Assistant custom integration)

Hermes Conversation Agent is a Home Assistant custom integration that registers a conversation entity and forwards user utterances to a Hermes gateway using an OpenAI-compatible chat completions endpoint.

## Features

- Home Assistant config flow (`host`, optional `api_key`, `verify_ssl`)
- Conversation agent entity selectable in Voice Assistants
- Preserves conversation continuity via `conversation_id`
- Options flow for `model`, `system_prompt`, `timeout`, and `max_history`
- Safe handling for auth errors, timeouts, and transient gateway failures

## Repository layout

- `custom_components/hermes_conversation/manifest.json`
- `custom_components/hermes_conversation/__init__.py`
- `custom_components/hermes_conversation/config_flow.py`
- `custom_components/hermes_conversation/conversation.py`
- `custom_components/hermes_conversation/api.py`
- `custom_components/hermes_conversation/strings.json`
- `hacs.json`

## Installation

### HACS (custom repository)

1. In Home Assistant, open HACS -> Integrations -> menu -> Custom repositories.
2. Add `https://github.com/tilarso/hermes-conversation-agent` with category `Integration`.
3. Install `Hermes Conversation Agent`.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/hermes_conversation` into your HA config directory.
2. Restart Home Assistant.

## Setup

1. Home Assistant -> Settings -> Devices & services -> Add Integration.
2. Search `Hermes Conversation Agent`.
3. Enter:
   - `Hermes URL` (example `http://192.168.1.74:8765`)
   - `API key` (optional)
   - `Verify SSL` (disable only for self-signed cert setups)
4. Open Voice Assistants settings and select `Hermes` as conversation agent.

## Development notes

- The integration posts to `<host>/v1/chat/completions` with `stream=false`.
- Health validation checks `<host>/api/health` then `<host>/health`.
- For MVP, thread continuity is mapped 1:1 from HA `conversation_id` to Hermes `thread_id`.

## Tests

Run unit tests with:

python -m pytest -q
