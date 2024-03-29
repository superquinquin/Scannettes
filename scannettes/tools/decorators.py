from functools import wraps
from typing import Optional
from time import perf_counter

from flask import current_app, redirect, request, url_for

from scannettes.tools.authenticator import Authenticator


def protected(auth_level: Optional[str]):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            authenticator = current_app.cache.config["authenticator"]
            if Authenticator.authorize(authenticator, request, auth_level):
                return f(*args, **kwargs)
            return redirect(url_for("scannettes_bp.login"))
        return wrapped
    return decorator


def logging_hook(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        tick = perf_counter()
        logging = current_app.logger
        r = request
        try:
            out = f(*args, **kwargs)
            perf = round(perf_counter() - tick, 5)
            logging.info(f"{r.method} [200][{r.sid}][{f.__module__}.{f.__name__}][{perf}s]")
        except Exception as e:
            out = None
            logging.error(f"[500][{f.__module__}.{f.__name__}][{args}][{kwargs}]")
            logging.exception(e, exc_info=True)
        return out
    return wrapped
