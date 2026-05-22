"""Tests for Hermes API client helpers."""

from __future__ import annotations

from custom_components.hermes_conversation.api import extract_assistant_text


def test_extract_assistant_text_from_openai_shape() -> None:
    data = {"choices": [{"message": {"content": "hello from hermes"}}]}
    assert extract_assistant_text(data) == "hello from hermes"


def test_extract_assistant_text_from_fallback_key() -> None:
    data = {"response": "fallback response"}
    assert extract_assistant_text(data) == "fallback response"


def test_extract_assistant_text_empty_when_no_supported_shape() -> None:
    assert extract_assistant_text({"foo": "bar"}) == ""
