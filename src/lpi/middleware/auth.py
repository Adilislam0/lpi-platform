"""Auth middleware — Phase 2 stub.

Phase 2: get_current_user() always returns "default_user".
         No token parsing, no request blocking, pure no-op.

Phase 3 swap (do not change any route file — only this function):
    import jwt
    from fastapi import HTTPException
    from lpi.config import settings

    def get_current_user(token: str = "") -> str:
        if not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        try:
            payload = jwt.decode(
                token.removeprefix("Bearer "),
                settings.jwt_secret,
                algorithms=["HS256"],
            )
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
"""


def get_current_user(token: str = "") -> str:
    """Return the current user's ID.

    Phase 2: ignores `token` entirely; always returns "default_user".
    Every route that needs the caller identity calls THIS function —
    never hard-codes the string — so Phase 3 is a one-function change.
    """
    return "default_user"