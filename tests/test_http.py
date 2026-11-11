"""Exercise the client against a local HTTP server, never a live home."""

from unittest.mock import AsyncMock, patch
import gzip

import aiohttp
from aiohttp import web
import pytest

from custom_components.hermes_conversation.api import (
    HermesAuthError,
    HermesClient,
    HermesUnavailableError,
    extract_assistant_text,
)


@pytest.fixture
async def backend(aiohttp_server):
    async def create(handler):
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", handler)
        return await aiohttp_server(app)
    return create


def make_client(session, server):
    return HermesClient(session, str(server.make_url("")), "test-key", True, 5)


async def test_chat_payload_and_response_over_http(backend):
    requests = []

    async def handler(request):
        requests.append((request.path, request.headers.get("Authorization"), await request.json()))
        return web.json_response({"choices": [{"message": {"content": "Hello"}}]})

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        client = make_client(session, server)
        client.system_prompt = "Be concise"
        assert await client.send_message("hi", "session", [{"role": "user", "content": "before"}]) == "Hello"
    path, auth, payload = requests[0]
    assert path == "/v1/chat/completions"
    assert auth == "Bearer test-key"
    assert payload["thread_id"] == payload["conversation_id"] == "session"
    assert payload["stream"] is False
    assert payload["messages"] == [
        {"role": "system", "content": "Be concise"},
        {"role": "user", "content": "before"},
        {"role": "user", "content": "hi"},
    ]


async def test_health_falls_back_when_legacy_path_missing(backend):
    paths = []

    async def handler(request):
        paths.append(request.path)
        if request.path == "/api/health":
            return web.Response(status=404)
        return web.json_response({"status": "ok"})

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        assert await make_client(session, server).health_check() == {"status": "ok"}
    assert paths == ["/api/health", "/health"]


async def test_health_does_not_mask_authentication_failure(backend):
    async def handler(request):
        return web.Response(status=401)

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(HermesAuthError):
            await make_client(session, server).health_check()


async def test_chat_is_not_replayed_after_server_error(backend, caplog):
    calls = []

    async def handler(request):
        calls.append(request.path)
        return web.Response(status=503, text="private transcript and credentials")

    server = await backend(handler)
    caplog.set_level("DEBUG", logger="custom_components.hermes_conversation.api")
    async with aiohttp.ClientSession() as session:
        with pytest.raises(HermesUnavailableError):
            await make_client(session, server).send_message("hi", "session")
    assert len(calls) == 1
    assert "private transcript and credentials" not in caplog.text


@pytest.mark.parametrize("header", ["invalid", "-3", "NaN", "Infinity", "Wed, 21 Oct 2015 07:28:00 GMT"])
async def test_health_retry_after_is_safe(backend, header):
    calls = []

    async def handler(request):
        calls.append(request.path)
        if len(calls) == 1:
            return web.Response(status=503, headers={"Retry-After": header})
        return web.json_response({"status": "ok"})

    server = await backend(handler)
    with patch("custom_components.hermes_conversation.api.asyncio.sleep", new_callable=AsyncMock) as sleep:
        async with aiohttp.ClientSession() as session:
            assert await make_client(session, server).health_check() == {"status": "ok"}
    assert len(calls) == 2
    assert 0 <= sleep.call_args.args[0] <= 5


@pytest.mark.parametrize("payload", [[], None, "text", {"choices": [None]}, {"choices": [{"message": None}]}])
async def test_malformed_success_response_is_handled(backend, payload):
    async def handler(request):
        return web.json_response(payload)

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(HermesUnavailableError):
            await make_client(session, server).send_message("hi", "session")


async def test_redirect_is_not_followed(backend):
    paths = []

    async def handler(request):
        paths.append(request.path)
        if request.path != "/unexpected":
            raise web.HTTPTemporaryRedirect("/unexpected")
        return web.json_response({"response": "should not reach this"})

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(HermesUnavailableError):
            await make_client(session, server).send_message("hi", "session")
    assert paths == ["/v1/chat/completions"]


@pytest.mark.parametrize("payload", [None, [], {"choices": [None]}, {"choices": [{"message": None}]}])
def test_text_extractor_rejects_malformed_shapes(payload):
    assert extract_assistant_text(payload) == ""


@pytest.mark.parametrize("encoding", ["plain", "gzip", "chunked"])
async def test_oversized_response_is_rejected(backend, encoding):
    body = b'{"response":"' + b"x" * (1024 * 1024) + b'"}'

    async def handler(request):
        if encoding == "gzip":
            return web.Response(body=gzip.compress(body), content_type="application/json", headers={"Content-Encoding": "gzip"})
        if encoding == "chunked":
            response = web.StreamResponse(headers={"Content-Type": "application/json"})
            await response.prepare(request)
            for offset in range(0, len(body), 65536):
                await response.write(body[offset:offset + 65536])
            await response.write_eof()
            return response
        return web.Response(body=body, content_type="application/json")

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(HermesUnavailableError, match="too large"):
            await make_client(session, server).send_message("hi", "session")


async def test_health_does_not_mask_server_failure_with_public_fallback(backend):
    paths = []

    async def handler(request):
        paths.append(request.path)
        if request.path == "/api/health":
            return web.Response(status=503)
        return web.json_response({"status": "ok"})

    server = await backend(handler)
    with patch("custom_components.hermes_conversation.api.asyncio.sleep", new_callable=AsyncMock):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(HermesUnavailableError):
                await make_client(session, server).health_check()
    assert paths == ["/api/health", "/api/health"]


@pytest.mark.parametrize("body", [b"{broken json", b'\xff', b"[" * 2000 + b"]" * 2000])
async def test_invalid_json_does_not_escape_client_error_handling(backend, body):
    async def handler(request):
        return web.Response(body=body, content_type="application/json")

    server = await backend(handler)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(HermesUnavailableError, match="Hermes returned"):
            await make_client(session, server).send_message("hi", "session")
