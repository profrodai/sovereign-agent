"""HMAC-SHA256 envelope signatures over canonical unsigned bytes."""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from dataclasses import dataclass

from sovereign_agent.contracts._core import canonical_json_bytes

from .envelope import ProtocolEnvelope, ProtocolError


@dataclass(frozen=True)
class Keyring:
    """Configured caller keys. Possession proves identity, not ZEO authority."""

    secrets: Mapping[str, bytes]

    def secret(self, key_id: str) -> bytes:
        try:
            return self.secrets[key_id]
        except KeyError as exc:
            raise ProtocolError("unauthenticated", detail=f"unknown key_id {key_id!r}") from exc


def signature_for(envelope: ProtocolEnvelope, secret: bytes) -> str:
    digest = hmac.new(secret, canonical_json_bytes(envelope.unsigned_dict()), "sha256")
    return digest.hexdigest()


def sign(envelope: ProtocolEnvelope, keyring: Keyring) -> ProtocolEnvelope:
    secret = keyring.secret(envelope.auth.key_id)
    auth = envelope.auth
    object.__setattr__(auth, "signature", signature_for(envelope, secret))
    return envelope


def signed_copy(envelope: ProtocolEnvelope, keyring: Keyring) -> ProtocolEnvelope:
    from dataclasses import replace

    secret = keyring.secret(envelope.auth.key_id)
    signature = signature_for(envelope, secret)
    return replace(envelope, auth=replace(envelope.auth, signature=signature))


def verify(envelope: ProtocolEnvelope, keyring: Keyring) -> None:
    secret = keyring.secret(envelope.auth.key_id)
    expected = signature_for(envelope, secret)
    if not hmac.compare_digest(expected, envelope.auth.signature):
        raise ProtocolError("unauthenticated", detail="HMAC signature mismatch")
