"""ZeroClaw webhook HMAC-SHA256 signature verification.

ZeroClaw confirmed (June 27, 2026) they will use HMAC-SHA256 — their CLI
signs every POST payload with the shared secret and includes the signature
in the X-ZeroClaw-Signature header as: sha256=<hex_digest>

Usage in the webhook route:
    body = await verify_zeroclaw_signature(request)
    payload = json.loads(body)

On failure: raises 401 HTTPException — nothing is stored, attempt is logged.
"""

import hashlib
import hmac
import logging

from fastapi import HTTPException, Request

from lpi.config import settings

logger = logging.getLogger(__name__)


async def verify_zeroclaw_signature(request: Request) -> bytes:
    """Verify HMAC-SHA256 signature on an incoming ZeroClaw webhook request.

    ZeroClaw includes the signature as:
        X-ZeroClaw-Signature: sha256=<hex_digest>

    We recompute the HMAC over the raw request body using our shared secret
    and compare with constant-time comparison (hmac.compare_digest) to
    prevent timing attacks.

    Returns:
        bytes — the raw request body, ready to be JSON-parsed by the caller.

    Raises:
        HTTPException 401 — if the header is missing or the signature is wrong.
    """
    signature_header = request.headers.get("X-ZeroClaw-Signature")

    if not signature_header:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            "ZeroClaw webhook received with no signature header from %s", client_ip
        )
        raise HTTPException(
            status_code=401,
            detail="Missing X-ZeroClaw-Signature header.",
        )

    body = await request.body()

    secret = settings.zeroclaw_webhook_secret.encode("utf-8")
    expected_digest = hmac.new(secret, body, hashlib.sha256).hexdigest()

    # Strip the "sha256=" prefix ZeroClaw sends
    actual_digest = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(expected_digest, actual_digest):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            "ZeroClaw webhook signature mismatch from %s — possible spoofed request",
            client_ip,
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid ZeroClaw signature.",
        )

    return body
