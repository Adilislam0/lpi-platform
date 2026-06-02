"""Auth middleware stub — Phase 1 / Phase 2 scaffold.

Owner : Jaivardhan Singh
Task  : B (lead's assignment — Day 1)

Phase 1 / Phase 2:
    get_current_user(token) always returns "default_user".
    No JWT decoding. No request blocking. Pure no-op stub.

Phase 3 (Jaivardhan implements this):
    Decode the Bearer token from the Authorization header.
    Return the `sub` claim as the user ID.
    Raise HTTPException(401) on invalid / expired tokens.
    Implementation swap — only THIS function changes.
    No route file needs to be touched.

──────────────────────────────────────────────────────────────────
Phase 3 swap (copy this block in when Danial confirms JWT secret):

    import jwt  # pip install python-jose[cryptography]
    from fastapi import HTTPException
    from lpi.config import settings

    def get_current_user(token: str) -> str:
        if not token:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,        # add to config.py in Phase 3
                algorithms=["HS256"],
            )
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
──────────────────────────────────────────────────────────────────
"""


def get_current_user(token: str = "") -> str:
    """Extract and return the current user ID from a bearer token.

    Phase 1 / Phase 2: ignores token entirely; always returns "default_user".
    Phase 3: decodes the JWT and returns the `sub` claim.

    Args:
        token: The raw bearer token string from the Authorization header.
               Pass an empty string (or omit) when calling without auth context.

    Returns:
        User ID string — "default_user" in Phase 1/2.
    """
    # Phase 3: replace this line with JWT decode logic (see module docstring)
    return "default_user"