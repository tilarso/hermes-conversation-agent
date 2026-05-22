"""Test stubs for Home Assistant imports."""

from __future__ import annotations

import sys
import types


def _install_homeassistant_stubs() -> None:
    if "homeassistant" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")

    components = types.ModuleType("homeassistant.components")
    conversation = types.ModuleType("homeassistant.components.conversation")

    class ConversationEntity:
        pass

    class ConversationEntityFeature:
        CONTROL = 1

    class ConversationResult:
        def __init__(self, response, conversation_id):
            self.response = response
            self.conversation_id = conversation_id

    class ConversationInput:
        def __init__(self, text: str, conversation_id: str | None = None, language: str = "en"):
            self.text = text
            self.conversation_id = conversation_id
            self.language = language

    conversation.ConversationEntity = ConversationEntity
    conversation.ConversationEntityFeature = ConversationEntityFeature
    conversation.ConversationResult = ConversationResult
    conversation.ConversationInput = ConversationInput

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        def __init__(self, entry_id: str = "entry"):
            self.entry_id = entry_id
            self.options = {}
            self.data = {}

    class ConfigFlow:
        async def async_set_unique_id(self, _unique_id):
            return None

        def _abort_if_unique_id_configured(self):
            return None

        def async_create_entry(self, *, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(self, *, step_id, data_schema=None, errors=None):
            return {
                "type": "form",
                "step_id": step_id,
                "errors": errors or {},
                "data_schema": data_schema,
            }

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__()

    class OptionsFlow:
        def async_create_entry(self, *, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(self, *, step_id, data_schema=None, errors=None):
            return {
                "type": "form",
                "step_id": step_id,
                "errors": errors or {},
                "data_schema": data_schema,
            }

    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigFlow = ConfigFlow
    config_entries.OptionsFlow = OptionsFlow

    const = types.ModuleType("homeassistant.const")
    const.MATCH_ALL = "*"
    const.CONF_API_KEY = "api_key"
    const.CONF_HOST = "host"

    class Platform:
        CONVERSATION = "conversation"

    const.Platform = Platform

    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:
        pass

    def callback(func):
        return func

    core.HomeAssistant = HomeAssistant
    core.callback = callback

    data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
    data_entry_flow.FlowResult = dict

    voluptuous = types.ModuleType("voluptuous")

    class _DummyRange:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _DummyAll:
        def __init__(self, *args):
            self.args = args

    def _schema(payload):
        return payload

    def _required(key):
        return key

    def _optional(key, default=None):
        return key

    def _coerce(_type):
        return _type

    voluptuous.Schema = _schema
    voluptuous.Required = _required
    voluptuous.Optional = _optional
    voluptuous.All = _DummyAll
    voluptuous.Coerce = _coerce
    voluptuous.Range = _DummyRange

    helpers = types.ModuleType("homeassistant.helpers")
    aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")

    def async_get_clientsession(_hass):
        return None

    aiohttp_client.async_get_clientsession = async_get_clientsession

    entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
    entity_platform.AddEntitiesCallback = object

    intent = types.ModuleType("homeassistant.helpers.intent")

    class IntentResponse:
        def __init__(self, language: str | None = None):
            self.language = language
            self.speech = None

        def async_set_speech(self, speech: str) -> None:
            self.speech = speech

    intent.IntentResponse = IntentResponse

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.components"] = components
    sys.modules["homeassistant.components.conversation"] = conversation
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.const"] = const
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.data_entry_flow"] = data_entry_flow
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client
    sys.modules["voluptuous"] = voluptuous
    sys.modules["homeassistant.helpers.entity_platform"] = entity_platform
    sys.modules["homeassistant.helpers.intent"] = intent


_install_homeassistant_stubs()
