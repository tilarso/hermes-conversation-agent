"""Hermes HTTP client for Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
from typing import Any

import aiohttp


class HermesApiError(Exception):
    """Base Hermes API error."""


class HermesAuthError(HermesApiError):
    """Authentication failed."""


class HermesUnavailableError(HermesApiError):
    """Gateway unavailable or returned an unexpected response."""


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

        last_error: Exception | None = None
        for url in urls:
            try:
                return await self._request("GET", url)
            except HermesApiError as err:
                last_error = err
        raise HermesUnavailableError("Hermes health endpoint is unavailable") from last_error

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
        retries = 1

        for attempt in range(retries + 1):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=self._headers,
                    json=json,
                    ssl=self.verify_ssl,
                    timeout=timeout,
                ) as resp:
                    if resp.status in (401, 403):
                        raise HermesAuthError("Authentication failed")

                    if resp.status in (429, 500, 502, 503, 504) and attempt < retries:
                        retry_after = resp.headers.get("Retry-After")
                        delay = min(float(retry_after), 5.0) if retry_after else 1.0
                        await asyncio.sleep(delay)
                        continue

                    if resp.status >= 400:
                        body = await resp.text()
                        raise HermesUnavailableError(f"Hermes HTTP {resp.status}: {body[:200]}")

                    try:
                        return await resp.json()
                    except (aiohttp.ContentTypeError, ValueError) as err:
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
    if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
        message = data["choices"][0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content.strip()

    for key in ("response", "text", "content", "message"):
        value = data.get(key)
        if isinstance(value, str):
            return value.strip()

    return ""
