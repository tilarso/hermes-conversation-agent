"""Config flow for Hermes Conversation Agent."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HermesAuthError, HermesClient, HermesTimeoutError, HermesUnavailableError, validate_host
from .const import (
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


class HermesConversationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hermes Conversation Agent."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                validate_host(user_input[CONF_HOST])
            except ValueError:
                return self.async_show_form(
                    step_id="user", data_schema=_user_schema(), errors={"base": "invalid_url"}
                )
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            client = HermesClient(
                session=async_get_clientsession(self.hass),
                host=user_input[CONF_HOST],
                api_key=user_input.get(CONF_API_KEY) or None,
                verify_ssl=user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                timeout=DEFAULT_TIMEOUT,
            )

            try:
                await client.health_check()
            except HermesAuthError:
                errors["base"] = "auth"
            except HermesTimeoutError:
                errors["base"] = "timeout"
            except HermesUnavailableError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="Hermes Conversation Agent",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                        CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                    },
                )

        return self.async_show_form(step_id="user", data_schema=_user_schema(), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return HermesConversationOptionsFlow()


class HermesConversationOptionsFlow(config_entries.OptionsFlowWithReload):
    """Options flow for Hermes Conversation Agent."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(step_id="init", data_schema=_options_schema(options))


def _user_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_API_KEY, default=""): str,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
        }
    )


def _options_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_MODEL, default=options.get(CONF_MODEL, "")): str,
            vol.Optional(
                CONF_SYSTEM_PROMPT,
                default=options.get(CONF_SYSTEM_PROMPT, ""),
            ): str,
            vol.Optional(CONF_TIMEOUT, default=options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): vol.All(
                vol.Coerce(int), vol.Range(min=5, max=120)
            ),
            vol.Optional(
                CONF_MAX_HISTORY,
                default=options.get(CONF_MAX_HISTORY, DEFAULT_MAX_HISTORY),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
        }
    )
