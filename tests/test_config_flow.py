"""Tests for config flow behavior."""

from __future__ import annotations

import types

import pytest

from custom_components.hermes_conversation import config_flow


@pytest.mark.asyncio
async def test_config_flow_user_step_success(monkeypatch) -> None:
    flow = config_flow.HermesConversationConfigFlow()
    flow.hass = object()

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
async def test_config_flow_user_step_cannot_connect(monkeypatch) -> None:
    flow = config_flow.HermesConversationConfigFlow()
    flow.hass = object()

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
