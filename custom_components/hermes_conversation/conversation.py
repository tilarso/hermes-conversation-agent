"""Conversation entity platform for Hermes Conversation Agent."""

from __future__ import annotations

from collections import defaultdict, deque
import uuid

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.intent import IntentResponse

from .api import HermesAuthError, HermesClient, HermesTimeoutError, HermesUnavailableError
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hermes conversation entity from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HermesConversationEntity(
                entry=entry,
                client=data["client"],
                max_history=data["max_history"],
            )
        ]
    )


class HermesConversationEntity(conversation.ConversationEntity):
    """A Home Assistant conversation agent backed by Hermes."""

    _attr_has_entity_name = True
    _attr_name = "Hermes"
    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, entry: ConfigEntry, client: HermesClient, max_history: int) -> None:
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        self._client = client
        self._max_history = max_history
        self._history: dict[str, deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=max(self._max_history * 2, 2))
        )

    @property
    def supported_languages(self) -> list[str] | str:
        return MATCH_ALL

    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Process user input through Hermes and return a conversation result."""
        conversation_id = user_input.conversation_id or str(uuid.uuid4())
        history = list(self._history[conversation_id])

        try:
            text = await self._client.send_message(
                text=user_input.text,
                conversation_id=conversation_id,
                history=history,
            )
        except HermesAuthError:
            text = "Hermes authentication failed. Check API key in integration settings."
        except HermesTimeoutError:
            text = "Hermes did not respond in time. Please try again."
        except HermesUnavailableError:
            text = "Hermes is currently unreachable. Please try again shortly."

        self._history[conversation_id].append({"role": "user", "content": user_input.text})
        self._history[conversation_id].append({"role": "assistant", "content": text})

        response = IntentResponse(language=user_input.language)
        response.async_set_speech(text)

        return conversation.ConversationResult(
            response=response,
            conversation_id=conversation_id,
        )

    async def async_prepare(self, language: str | None = None) -> None:
        """Prepare entity for use (no-op for MVP)."""
        return
