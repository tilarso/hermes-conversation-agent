"""Tests for conversation entity behavior."""

from __future__ import annotations

import pytest

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


class FakeConversationInput:
    def __init__(self, text: str, conversation_id: str | None = None, language: str = "en") -> None:
        self.text = text
        self.conversation_id = conversation_id
        self.language = language


@pytest.mark.asyncio
async def test_entity_process_sets_and_reuses_conversation_id() -> None:
    client = FakeClient()
    entity = HermesConversationEntity(DummyEntry(), client, max_history=10)

    result1 = await entity.async_process(FakeConversationInput("hello"))
    conv_id = result1.conversation_id

    result2 = await entity.async_process(FakeConversationInput("again", conversation_id=conv_id))

    assert result1.conversation_id
    assert result2.conversation_id == conv_id
    assert client.calls[1]["history"][0]["content"] == "hello"
    assert client.calls[1]["history"][1]["content"] == "echo:hello"
