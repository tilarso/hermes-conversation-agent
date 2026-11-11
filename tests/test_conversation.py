"""Tests for conversation entity behavior."""

from __future__ import annotations

import asyncio
import pytest
from homeassistant.components import conversation
from homeassistant.components.conversation.chat_log import DATA_CHAT_LOGS
from homeassistant.core import Context

from custom_components.hermes_conversation.conversation import HermesConversationEntity


class DummyEntry:
    entry_id = "entry-1"


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def send_message(self, text: str, conversation_id: str, history=None) -> str:
        self.calls.append(
            {
                "text": text,
                "conversation_id": conversation_id,
                "history": history or [],
            }
        )
        return f"echo:{text}"


def make_input(text, conversation_id=None, user_id=None):
    return conversation.ConversationInput(
        text=text, context=Context(user_id=user_id), conversation_id=conversation_id,
        device_id=None, satellite_id=None, language="en", agent_id="conversation.hermes",
    )


@pytest.mark.asyncio
async def test_entity_process_sets_and_reuses_conversation_id(hass) -> None:
    client = FakeClient()
    entity = HermesConversationEntity(DummyEntry(), client, max_history=10)
    entity.hass = hass

    result1 = await entity.async_process(make_input("hello"))
    conv_id = result1.conversation_id

    result2 = await entity.async_process(make_input("again", conversation_id=conv_id))

    assert result1.conversation_id
    assert result2.conversation_id == conv_id
    assert client.calls[1]["history"][0]["content"] == "hello"
    assert client.calls[1]["history"][1]["content"] == "echo:hello"
    assert hass.data[DATA_CHAT_LOGS][conv_id].content[-1].content == "echo:again"


async def test_outbound_history_is_bounded(hass, entry, client):
    entity = HermesConversationEntity(entry, client, max_history=1)
    entity.hass = hass
    first = await entity.async_process(make_input("first"))
    await entity.async_process(make_input("second", first.conversation_id))
    await entity.async_process(make_input("third", first.conversation_id))
    assert client.send_message.call_args.kwargs["history"] == [
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "Hello from Hermes"},
    ]


async def test_session_cannot_be_reused_by_another_user(hass, entry, client):
    from homeassistant.exceptions import Unauthorized

    entity = HermesConversationEntity(entry, client, max_history=10)
    entity.hass = hass
    first = await entity.async_process(make_input("private", user_id="alice"))
    with pytest.raises(Unauthorized):
        await entity.async_process(make_input("leak", first.conversation_id, user_id="bob"))
    assert client.send_message.await_count == 1


async def test_backend_error_returns_intent_error(hass, entry, client):
    from custom_components.hermes_conversation.api import HermesTimeoutError

    entity = HermesConversationEntity(entry, client, max_history=10)
    entity.hass = hass
    client.send_message.side_effect = HermesTimeoutError("private upstream details")
    result = await entity.async_process(make_input("hello"))
    response = result.response.as_dict()
    assert response["response_type"] == "error"
    assert "private upstream details" not in str(response)


async def test_overlapping_turns_do_not_replay_or_mix_history(hass, entry, client):
    entity = HermesConversationEntity(entry, client, max_history=10)
    entity.hass = hass
    first = await entity.async_process(make_input("first"))
    started = asyncio.Event()
    release = asyncio.Event()

    async def delayed_reply(**kwargs):
        started.set()
        await release.wait()
        return "Finished"

    client.send_message.side_effect = delayed_reply
    pending = asyncio.create_task(entity.async_process(make_input("second", first.conversation_id)))
    try:
        await asyncio.wait_for(started.wait(), timeout=2)
        with pytest.raises(conversation.ConversationBusyError):
            await entity.async_process(make_input("third", first.conversation_id))
    finally:
        release.set()
        await pending
    assert client.send_message.await_count == 2
