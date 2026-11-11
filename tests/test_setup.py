"""Load the real HA conversation platform and exercise its public API."""

from unittest.mock import AsyncMock, patch

from homeassistant.auth import auth_manager_from_config
from homeassistant.components import conversation
from homeassistant.core import Context
from homeassistant.setup import async_setup_component

from custom_components.hermes_conversation.const import DOMAIN


async def test_platform_load_converse_and_unload(hass, entry, unused_tcp_port):
    hass.auth = await auth_manager_from_config(hass, [], [])
    assert await async_setup_component(hass, "conversation", {"http": {"server_port": unused_tcp_port}})
    with patch("custom_components.hermes_conversation.api.HermesClient.send_message", new_callable=AsyncMock, return_value="Hello from Hermes") as send:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        states = hass.states.async_all("conversation")
        hermes = next(state for state in states if state.attributes.get("friendly_name") == "Hermes")
        result = await conversation.async_converse(
            hass, text="hello", conversation_id=None, context=Context(),
            language="en", agent_id=hermes.entity_id,
        )
        assert result.response.speech["plain"]["speech"] == "Hello from Hermes"
        assert send.call_args.kwargs["conversation_id"] == result.conversation_id
        assert entry.entry_id in hass.data[DOMAIN]
        options_flow = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.config_entries.options.async_configure(options_flow["flow_id"], {
            "model": "new-model", "system_prompt": "Be brief", "timeout": 45, "max_history": 3,
        })
        await hass.async_block_till_done()
        assert hass.data[DOMAIN][entry.entry_id]["client"].model == "new-model"
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert hass.states.get(hermes.entity_id).state == "unavailable"
        assert entry.entry_id not in hass.data[DOMAIN]
