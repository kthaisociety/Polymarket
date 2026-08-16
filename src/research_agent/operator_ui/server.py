"""Dependency-free local HTTP server for the read-only research library."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final, cast
from urllib.parse import urlsplit

from research_agent.operator_ui.projection import (
    ResearchLibraryProjection,
    build_research_library,
)

_ASSET_ROOT: Final = Path(__file__).with_name("assets")
_MAX_PORT: Final = 65_535
_ASSETS: Final[dict[str, tuple[str, str]]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class ResearchLibraryServer(ThreadingHTTPServer):
    """HTTP server holding one immutable projection snapshot."""

    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        projection: ResearchLibraryProjection,
    ) -> None:
        """Initialize the server with one detached projection snapshot."""
        self.projection_json = json.dumps(
            projection.as_dict(), allow_nan=False, separators=(",", ":"), sort_keys=True
        ).encode()
        super().__init__(server_address, ResearchLibraryRequestHandler)


class ResearchLibraryRequestHandler(BaseHTTPRequestHandler):
    """Serve a fixed asset allow-list and one read-only JSON endpoint."""

    server_version = "ResearchLibrary/1"

    def do_GET(self) -> None:
        """Serve the immutable operator projection or fixed frontend assets."""
        path = urlsplit(self.path).path
        if path == "/health":
            self._send_json(b'{"status":"ok","mode":"read_only"}')
            return
        if path == "/api/library":
            server = cast("ResearchLibraryServer", self.server)
            self._send_json(server.projection_json)
            return
        asset = _ASSETS.get(path)
        if asset is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        filename, content_type = asset
        try:
            payload = (_ASSET_ROOT / filename).read_bytes()
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send(payload, content_type=content_type)

    def do_HEAD(self) -> None:
        """Return headers for known read-only routes."""
        path = urlsplit(self.path).path
        if path in {"/health", "/api/library"}:
            self._send(b"", content_type="application/json; charset=utf-8")
            return
        asset = _ASSETS.get(path)
        if asset is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send(b"", content_type=asset[1])

    def do_POST(self) -> None:
        """Reject state-changing requests."""
        self._method_not_allowed()

    def do_PUT(self) -> None:
        """Reject state-changing requests."""
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        """Reject state-changing requests."""
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        """Reject state-changing requests."""
        self._method_not_allowed()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Keep the local operator command quiet."""

    def _method_not_allowed(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, payload: bytes) -> None:
        self._send(payload, content_type="application/json; charset=utf-8")

    def _send(self, payload: bytes, *, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; object-src 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)


def serve_research_library(
    repository_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Build one projection and serve it until interrupted."""
    if not 0 <= port <= _MAX_PORT:
        message = f"Port must be between 0 and {_MAX_PORT}."
        raise ValueError(message)
    projection = build_research_library(repository_root)
    with ResearchLibraryServer((host, port), projection) as server:
        server.serve_forever(poll_interval=0.2)


__all__ = ["ResearchLibraryServer", "serve_research_library"]
