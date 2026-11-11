# PRIVACY: Do not log message content or user utterances.
"""Hermes HTTP client for Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json as json_module
import math
from typing import Any
from urllib.parse import urlsplit

import aiohttp

MAX_RESPONSE_BYTES = 1024 * 1024


def validate_host(host: str) -> None:
    """Allow explicit HTTP(S) backend URLs, including trusted LAN hosts."""
    try:
        parsed = urlsplit(host)
        valid = (
            parsed.scheme in ("http", "https")
            and parsed.hostname
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and "?" not in host
            and "#" not in host
            and not any(character.isspace() for character in host)
        )
        port = parsed.port
        if not valid or (port is not None and port == 0):
            raise ValueError
    except (ValueError, TypeError) as err:
        raise ValueError("Invalid Hermes URL") from err


class HermesApiError(Exception):
    """Base Hermes API error."""


class HermesAuthError(HermesApiError):
    """Authentication failed."""


class HermesUnavailableError(HermesApiError):
    """Gateway unavailable or returned an unexpected response."""


class HermesEndpointNotFoundError(HermesUnavailableError):
    """The backend does not provide this endpoint."""


class HermesTimeoutError(HermesApiError):
    """Gateway timed out."""


@dataclass(slots=True)
class HermesClient:
    """Simple async Hermes API wrapper."""

    session: aiohttp.ClientSession
    host: str
    api_key: str | None
    verify_ssl: bool
    timeout: int
    model: str | None = None
    system_prompt: str | None = None

    def __post_init__(self) -> None:
        validate_host(self.host)

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @property
    def _chat_url(self) -> str:
        return f"{self.host.rstrip('/')}/v1/chat/completions"

    async def health_check(self) -> dict[str, Any]:
        """Check Hermes health endpoint for config flow validation."""
        urls = [
            f"{self.host.rstrip('/')}/api/health",
            f"{self.host.rstrip('/')}/health",
        ]

        for index, url in enumerate(urls):
            try:
                return await self._request("GET", url)
            except HermesEndpointNotFoundError:
                if index == len(urls) - 1:
                    raise
        raise HermesUnavailableError("Hermes health endpoint is unavailable")

    async def send_message(
        self,
        text: str,
        conversation_id: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Send user utterance to Hermes and return assistant text."""
        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": text})

        payload: dict[str, Any] = {
            "messages": messages,
            "conversation_id": conversation_id,
            "thread_id": conversation_id,
            "stream": False,
        }
        if self.model:
            payload["model"] = self.model

        data = await self._request("POST", self._chat_url, json=payload)
        assistant_text = extract_assistant_text(data)
        if not assistant_text:
            raise HermesUnavailableError("Hermes returned an empty response")
        return assistant_text

    async def _request(self, method: str, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        # A chat completion may already have executed tools before failing.
        # Without server-side idempotency, only read-only GETs may be retried.
        retries = 1 if method == "GET" else 0

        for attempt in range(retries + 1):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=self._headers,
                    json=json,
                    ssl=self.verify_ssl,
                    timeout=timeout,
                    allow_redirects=False,
                ) as resp:
                    if resp.status in (401, 403):
                        raise HermesAuthError("Authentication failed")

                    if resp.status in (429, 500, 502, 503, 504) and attempt < retries:
                        retry_after = resp.headers.get("Retry-After")
                        try:
                            delay = float(retry_after) if retry_after else 1.0
                        except ValueError:
                            delay = 1.0
                        delay = min(max(delay, 0.0), 5.0) if math.isfinite(delay) else 1.0
                        await asyncio.sleep(delay)
                        continue

                    if resp.status in (404, 405):
                        raise HermesEndpointNotFoundError("Hermes endpoint is unavailable")
                    if resp.status >= 300:
                        # Response bodies can contain transcripts or secrets, even in debug logs.
                        raise HermesUnavailableError(f"Hermes HTTP error: {resp.status}")

                    if resp.content_type != "application/json" and not resp.content_type.endswith("+json"):
                        raise HermesUnavailableError("Hermes returned a non-JSON response")
                    # Bound decompressed bytes, including chunked responses. Do not
                    # trust Content-Length or read an unbounded body before checking.
                    body = bytearray()
                    async for chunk in resp.content.iter_chunked(65536):
                        if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                            raise HermesUnavailableError("Hermes response is too large")
                        body.extend(chunk)
                    try:
                        data = json_module.loads(body)
                        if not isinstance(data, dict):
                            raise HermesUnavailableError("Hermes returned an invalid response")
                        return data
                    except (ValueError, RecursionError) as err:
                        raise HermesUnavailableError("Hermes returned malformed JSON") from err
            except HermesApiError:
                raise
            except TimeoutError as err:
                raise HermesTimeoutError("Hermes request timed out") from err
            except aiohttp.ClientError as err:
                if attempt < retries:
                    await asyncio.sleep(1)
                    continue
                raise HermesUnavailableError("Hermes is unreachable") from err

        raise HermesUnavailableError("Hermes request failed")


def extract_assistant_text(data: dict[str, Any]) -> str:
    """Extract assistant text from known response shapes."""
    if not isinstance(data, dict):
        return ""
    choices = data.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()

    for key in ("response", "text", "content", "message"):
        value = data.get(key)
        if isinstance(value, str):
            return value.strip()

    return ""
