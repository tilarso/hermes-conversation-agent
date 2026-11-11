"""Fixtures using real Home Assistant classes, not framework stubs."""

from unittest.mock import AsyncMock

import pytest
import aiohttp

from homeassistant import loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant


from custom_components.hermes_conversation.const import DOMAIN


@pytest.fixture
async def hass(tmp_path, monkeypatch):
    """Provide an isolated HA instance; never connect to the user's instance."""
    instance = HomeAssistant(str(tmp_path))
    loader.async_setup(instance)

    # Keep HA's real HTTP client, but avoid mDNS/network discovery in tests.
    resolver = aiohttp.ThreadedResolver()
    monkeypatch.setattr(
        "homeassistant.helpers.aiohttp_client._async_get_or_create_resolver",
        lambda hass: resolver,
    )
    instance.config_entries = ConfigEntries(instance, {})
    assert await async_load_base_functionality(instance)
    yield instance
    await instance.async_stop(force=True)
    await resolver.close()


@pytest.fixture
def entry(hass):
    """Register a real config entry without starting an external backend."""
    config_entry = ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Hermes",
        data={"host": "https://hermes.example.com"},
        options={},
        source="user",
        unique_id="https://hermes.example.com",
        discovery_keys={},
        subentries_data=[],
    )
    hass.config_entries._entries[config_entry.entry_id] = config_entry
    return config_entry


@pytest.fixture
def client():
    """Mock only the Hermes network boundary."""
    return AsyncMock(send_message=AsyncMock(return_value="Hello from Hermes"))
