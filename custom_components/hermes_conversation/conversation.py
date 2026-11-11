"""Conversation entity platform for Hermes Conversation Agent."""

from __future__ import annotations

from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.intent import IntentResponse, IntentResponseErrorCode

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

    def __init__(self, entry: ConfigEntry, client: HermesClient, max_history: int) -> None:
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        self._client = client
        self._max_history = max_history

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return MATCH_ALL

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process user input through Hermes and return a conversation result."""
        # HA owns session IDs, user isolation, busy-turn checks, and expiration.
        # Send only bounded text history, excluding this turn's user message.
        history = [
            {"role": content.role, "content": content.content}
            for content in chat_log.content[:-1]
            if isinstance(content, (conversation.UserContent, conversation.AssistantContent))
            and content.content is not None
        ][-self._max_history * 2 :]

        try:
            text = await self._client.send_message(
                text=user_input.text,
                conversation_id=chat_log.conversation_id,
                history=history,
            )
        except (HermesAuthError, HermesTimeoutError, HermesUnavailableError) as err:
            if isinstance(err, HermesAuthError):
                text = "Hermes authentication failed. Check API key in integration settings."
            elif isinstance(err, HermesTimeoutError):
                text = "Hermes did not respond in time. Please try again."
            else:
                text = "Hermes is currently unavailable. Please try again shortly."
            response = IntentResponse(language=user_input.language)
            response.async_set_error(IntentResponseErrorCode.UNKNOWN, text)
            chat_log.async_add_assistant_content_without_tools(
                conversation.AssistantContent(agent_id=user_input.agent_id, content=text)
            )
            return conversation.ConversationResult(
                response=response, conversation_id=chat_log.conversation_id
            )

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(agent_id=user_input.agent_id, content=text)
        )
        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def async_prepare(self, language: str | None = None) -> None:
        """Prepare entity for use (no-op for MVP)."""
        return
