"""Local API transports: in-process and HTTP/1.1 over a Unix socket."""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any

from sovereign_agent.admission import AdmissionService
from sovereign_agent.api.envelope import (
    PROTOCOL_VERSION,
    SUPPORTED_VERSION_RANGE,
    ProtocolEnvelope,
    ProtocolError,
)
from sovereign_agent.api.idempotency import IdempotencyConflict, IdempotencyLedger
from sovereign_agent.api.signing import Keyring, signed_copy
from sovereign_agent.runtime import RuntimeRoot

Handler = Callable[[ProtocolEnvelope], dict[str, Any]]


@dataclass
class ApiResponse:
    status: int
    body: dict[str, Any]


class ApiDispatcher:
    def __init__(
        self,
        admission: AdmissionService,
        ledger: IdempotencyLedger,
        *,
        handlers: dict[str, Handler] | None = None,
    ) -> None:
        self.admission = admission
        self.ledger = ledger
        self.handlers = handlers or {}

    def register(self, kind: str, handler: Handler) -> None:
        self.handlers[kind] = handler

    def dispatch(self, envelope: ProtocolEnvelope, *, observer: bool = False) -> ApiResponse:
        try:
            if envelope.protocol_version.split(".")[0] != PROTOCOL_VERSION.split(".")[0]:
                raise ProtocolError(
                    "unsupported-version",
                    detail=f"major protocol mismatch: {envelope.protocol_version}",
                )
        except ProtocolError as exc:
            return ApiResponse(400, {**exc.to_dict()})
        decision = self.admission.admit(envelope, observer=observer)
        if not decision.allowed:
            status = 403 if decision.reason == "observer-forbidden" else 401
            if decision.reason == "unsupported-version":
                status = 400
            if decision.reason == "unknown-required-field":
                status = 400
            if decision.reason == "replay":
                status = 409
            return ApiResponse(
                status, {**decision.to_dict(), "supported_version_range": SUPPORTED_VERSION_RANGE}
            )
        handler = self.handlers.get(envelope.kind)
        if handler is None:
            return ApiResponse(
                400,
                {
                    "reason": "unsupported-kind",
                    "detail": envelope.kind,
                    "supported_version_range": SUPPORTED_VERSION_RANGE,
                },
            )
        idempotency_key = envelope.body.get("idempotency_key")
        try:
            result = handler(envelope)
        except ProtocolError as exc:
            return ApiResponse(400, exc.to_dict())
        if isinstance(idempotency_key, str) and idempotency_key:
            try:
                result = self.ledger.remember(idempotency_key, envelope.body, result)
            except IdempotencyConflict as exc:
                return ApiResponse(409, exc.to_dict())
        return ApiResponse(200, result)


class LocalTransport:
    """In-process test transport. Same dispatcher as the Unix-socket server."""

    def __init__(self, dispatcher: ApiDispatcher, keyring: Keyring) -> None:
        self.dispatcher = dispatcher
        self.keyring = keyring

    def send(self, envelope: ProtocolEnvelope, *, observer: bool = False) -> ApiResponse:
        signed = signed_copy(envelope, self.keyring) if envelope.auth.signature == "" else envelope
        try:
            parsed = ProtocolEnvelope.from_dict(signed.to_dict())
        except ProtocolError as exc:
            return ApiResponse(400, exc.to_dict())
        return self.dispatcher.dispatch(parsed, observer=observer)


class _UnixHTTPServer(ThreadingMixIn, HTTPServer):
    address_family = socket.AF_UNIX
    daemon_threads = True
    allow_reuse_address = True


def _handler_for(dispatcher: ApiDispatcher) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

        def _read_envelope(self) -> ProtocolEnvelope:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            return ProtocolEnvelope.from_dict(data)

        def _write(self, response: ApiResponse) -> None:
            payload = json.dumps(response.body, sort_keys=True).encode("utf-8")
            self.send_response(response.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            if self.path.rstrip("/") != "/v1/health":
                self._write(
                    ApiResponse(
                        404,
                        {"reason": "not-found", "supported_version_range": SUPPORTED_VERSION_RANGE},
                    )
                )
                return
            self._write(
                ApiResponse(
                    200,
                    {
                        "status": "ok",
                        "protocol_version": PROTOCOL_VERSION,
                        "supported_version_range": SUPPORTED_VERSION_RANGE,
                    },
                )
            )

        def do_POST(self) -> None:  # noqa: N802
            observer = self.headers.get("X-Sovereign-Observer", "").lower() == "true"
            if self.path.rstrip("/") != "/v1/messages":
                self._write(
                    ApiResponse(
                        404,
                        {"reason": "not-found", "supported_version_range": SUPPORTED_VERSION_RANGE},
                    )
                )
                return
            try:
                envelope = self._read_envelope()
            except ProtocolError as exc:
                self._write(ApiResponse(400, exc.to_dict()))
                return
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                self._write(
                    ApiResponse(
                        400,
                        {
                            "reason": "malformed-envelope",
                            "detail": str(exc),
                            "supported_version_range": SUPPORTED_VERSION_RANGE,
                        },
                    )
                )
                return
            self._write(dispatcher.dispatch(envelope, observer=observer))

    return Handler


class UnixSocketApiServer:
    def __init__(self, socket_path: Path, dispatcher: ApiDispatcher) -> None:
        self.socket_path = Path(socket_path)
        self.dispatcher = dispatcher
        self._server: _UnixHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self._server = _UnixHTTPServer(str(self.socket_path), _handler_for(self.dispatcher))  # type: ignore[arg-type]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self.socket_path.exists():
            self.socket_path.unlink()

    def __enter__(self) -> UnixSocketApiServer:
        self.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.stop()


class UnixSocketClient:
    def __init__(self, socket_path: Path) -> None:
        self.socket_path = Path(socket_path)

    def post(self, envelope: ProtocolEnvelope, *, observer: bool = False) -> ApiResponse:
        payload = json.dumps(envelope.to_dict(), sort_keys=True).encode("utf-8")
        observer_header = "true" if observer else "false"
        request = (
            b"POST /v1/messages HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(payload)}\r\n".encode("ascii")
            + f"X-Sovereign-Observer: {observer_header}\r\n".encode("ascii")
            + b"Connection: close\r\n\r\n"
            + payload
        )
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(str(self.socket_path))
            sock.sendall(request)
            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
        finally:
            sock.close()
        header, _, body = data.partition(b"\r\n\r\n")
        status_line = header.split(b"\r\n", 1)[0].decode("ascii")
        status = int(status_line.split(" ")[1])
        return ApiResponse(status, json.loads(body.decode("utf-8") or "{}"))


def build_local_stack(
    runtime_root: RuntimeRoot,
    keyring: Keyring,
    *,
    handlers: dict[str, Handler] | None = None,
) -> tuple[ApiDispatcher, LocalTransport]:
    from sovereign_agent.admission import AdmissionService
    from sovereign_agent.admission.auth import Authenticator

    authenticator = Authenticator(runtime_root, keyring)
    dispatcher = ApiDispatcher(
        AdmissionService(authenticator), IdempotencyLedger(runtime_root), handlers=handlers
    )
    return dispatcher, LocalTransport(dispatcher, keyring)
