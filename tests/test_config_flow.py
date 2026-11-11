"""Tests for config flow behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.hermes_conversation import config_flow


@pytest.mark.asyncio
async def test_config_flow_user_step_success(hass, monkeypatch) -> None:
    flow = config_flow.HermesConversationConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}

    async def fake_health_check(self):
        return {"status": "ok"}

    monkeypatch.setattr(config_flow.HermesClient, "health_check", fake_health_check)

    result = await flow.async_step_user(
        {
            "host": "http://hermes.local:8765",
            "api_key": "abc",
            "verify_ssl": False,
        }
    )

    assert result["type"] == "create_entry"
    assert result["data"]["host"] == "http://hermes.local:8765"


@pytest.mark.asyncio
async def test_config_flow_user_step_cannot_connect(hass, monkeypatch) -> None:
    flow = config_flow.HermesConversationConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}

    async def fake_health_check(self):
        raise config_flow.HermesUnavailableError("down")

    monkeypatch.setattr(config_flow.HermesClient, "health_check", fake_health_check)

    result = await flow.async_step_user(
        {
            "host": "http://hermes.local:8765",
            "api_key": "",
            "verify_ssl": True,
        }
    )

    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.parametrize("error, expected", [
    (config_flow.HermesAuthError, "auth"),
    (config_flow.HermesTimeoutError, "timeout"),
])
async def test_health_error_is_preserved(hass, monkeypatch, error, expected):
    flow = config_flow.HermesConversationConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}
    monkeypatch.setattr(config_flow.HermesClient, "health_check", AsyncMock(side_effect=error()))
    result = await flow.async_step_user({"host": "https://hermes.example.com"})
    assert result["errors"] == {"base": expected}


@pytest.mark.parametrize("host", ["file:///etc/passwd", "not-a-url", "https://", "https://user:pass@example.com", "https://example.com?token=secret", "https://example.com?", "https://example.com#"])
async def test_invalid_url_rejected_before_network(hass, host):
    flow = config_flow.HermesConversationConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}
    with patch.object(config_flow.HermesClient, "health_check", new_callable=AsyncMock) as health:
        result = await flow.async_step_user({"host": host})
    assert result["errors"] == {"base": "invalid_url"}
    health.assert_not_awaited()


async def test_options_saved_and_automatically_reloaded(hass, entry):
    from homeassistant import loader
    integration = await loader.async_get_integration(hass, entry.domain)
    await integration.async_get_platform("config_flow")
    with patch.object(hass.config_entries, "async_schedule_reload") as reload_entry:
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(result["flow_id"], {
            "model": "test-model", "system_prompt": "Be brief", "timeout": 45, "max_history": 3,
        })
    assert result["type"] == "create_entry"
    assert entry.options["model"] == "test-model"
    reload_entry.assert_called_once_with(entry.entry_id)
