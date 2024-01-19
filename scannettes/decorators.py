from functools import wraps
from typing import Optional

from flask import current_app, redirect, request

from scannettes.authenticator import Authenticator


def protected(auth_level: Optional[str]):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            authenticator = current_app.cache.config["authenticator"]
            token = request.cookies.get("session")
            try:
                auth = Authenticator(
                    **authenticator,
                ).verify_access(token)
            except Exception:
                auth = None

            if auth and auth_level in auth["authorizations"]:
                return f(*args, **kwargs)
            else:
                return redirect(request.headers.get("Referer"))

        return wrapped

    return decorator


def tracker(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        logger = current_app.logger
        try:
            out = f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
        return out

    return wrapped
