"""Adversarial tests for the local read-only operator server."""

from __future__ import annotations

import json
from email.message import Message
from http import HTTPStatus
from io import BytesIO

import pytest

from research_agent.operator_ui.server import (
    ResearchLibraryRequestHandler,
    ResearchLibraryServer,
)


def _request(method: str, path: str) -> tuple[int, dict[str, str], bytes]:
    server = object.__new__(ResearchLibraryServer)
    server.projection_json = json.dumps(
        {
            "library_kind": "READ_ONLY_RESEARCH_PROJECTION",
            "ongoing": [],
            "finalized": [],
        }
    ).encode()
    handler = object.__new__(ResearchLibraryRequestHandler)
    handler.server = server
    handler.client_address = ("127.0.0.1", 1)
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.command = method
    handler.path = path
    handler.headers = Message()
    handler.rfile = BytesIO()
    handler.wfile = BytesIO()
    routes = {
        "GET": handler.do_GET,
        "POST": handler.do_POST,
        "PUT": handler.do_PUT,
        "PATCH": handler.do_PATCH,
        "DELETE": handler.do_DELETE,
    }
    routes[method]()
    response = handler.wfile.getvalue()
    header_bytes, _, body = response.partition(b"\r\n\r\n")
    lines = header_bytes.decode().split("\r\n")
    status = int(lines[0].split()[1])
    headers = {
        key.strip(): value.strip()
        for line in lines[1:]
        if ":" in line
        for key, value in [line.split(":", 1)]
    }
    return status, headers, body


def test_server_exposes_two_view_shell_and_read_only_projection() -> None:
    """The shell and API expose exactly the two read-only library views."""
    status, headers, html = _request("GET", "/")
    assert status == HTTPStatus.OK
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Ongoing Research" in html
    assert b"Finalized Research Reports" in html

    status, headers, payload = _request("GET", "/api/library")
    assert status == HTTPStatus.OK
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    decoded = json.loads(payload)
    assert decoded["library_kind"] == "READ_ONLY_RESEARCH_PROJECTION"
    assert decoded["finalized"] == []


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_server_rejects_every_state_changing_method(method: str) -> None:
    """No HTTP mutation verb may cross the presentation boundary."""
    status, headers, body = _request(method, "/api/library")
    assert status == HTTPStatus.METHOD_NOT_ALLOWED
    assert headers["Allow"] == "GET, HEAD"
    assert body == b""


@pytest.mark.parametrize(
    "path",
    ["/../pyproject.toml", "/%2e%2e/pyproject.toml", "/research/secret.json", "/api"],
)
def test_server_fixed_allow_list_blocks_path_traversal(path: str) -> None:
    """Only fixed assets and fixed APIs are reachable from the server."""
    status, _, _ = _request("GET", path)
    assert status == HTTPStatus.NOT_FOUND
