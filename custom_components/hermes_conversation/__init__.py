"""The Hermes Conversation Agent integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HermesClient
from .const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_MAX_HISTORY,
    CONF_MODEL,
    CONF_SYSTEM_PROMPT,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    DEFAULT_MAX_HISTORY,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

PLATFORMS: list[Platform] = [Platform.CONVERSATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hermes Conversation Agent from a config entry."""
    data = {**entry.data, **entry.options}

    client = HermesClient(
        session=async_get_clientsession(hass),
        host=data[CONF_HOST],
        api_key=data.get(CONF_API_KEY),
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        timeout=int(data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
        model=data.get(CONF_MODEL) or None,
        system_prompt=data.get(CONF_SYSTEM_PROMPT) or None,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "max_history": int(data.get(CONF_MAX_HISTORY, DEFAULT_MAX_HISTORY)),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
