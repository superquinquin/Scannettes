from flask import Request, request, current_app, redirect

from typing import Optional, Callable
from functools import wraps

from cannettes_v2.authenticator import Authenticator

def protected(auth_level: Optional[str]):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            authenticator = current_app.cache["config"]["authenticator"]
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
    def wrapped(*args, **kwargs):
        
        # track status of the thread
        # log errors 
        return 0
    
    return wrapped