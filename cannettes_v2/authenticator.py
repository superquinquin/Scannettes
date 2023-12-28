
from yaml import load, SafeLoader
from hashlib import sha256
from typing import Dict, Any, Optional

from datetime import datetime
import jwt

from flask import Request, Response
from flask import redirect, url_for, make_response, current_app

class Authenticator(object):
    
    def __init__(
        self, 
        *,
        secret_key: Optional[str]= None, 
        salt: Optional[str]= None, 
        max_age: Optional[int]= None,
        users: Optional[Dict[str, Any]]= None,
        **kwargs
        ) -> None:
        self.secret_key = secret_key
        self.salt = salt
        self.max_age = max_age
        self.users = users

    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        sha = sha256(password.encode("utf-8")).hexdigest()
        if not self.users.get(username, None):
            return {"status": "failled", "reasons": "Unknown user"}
        
        if sha != self.users[username]["password"]:
            return {"status": "failled", "reasons": "Wrong password"}
        
        payload = {
            "content": f"{sha}{self.salt}{datetime.now()}",
            "authorizations": self.users[username]["authorizations"]
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return {"status": "success", "token": token, "cookie": self.write_cookie(token)}
        
        
        
    def load_users(self, users_path: str) -> Dict[str, Any]:
        with open(users_path, 'r') as f:
            users = load(f, SafeLoader)
        return users
    
    def write_cookie(self, token: str) -> str:
        max_age = f" Max-Age={self.max_age}" if self.max_age else ""
        return f"session={token};{max_age}"
        
        
    def verify_access(self, token: str):
        payload = jwt.decode(token, self.secret_key, algorithms="HS256")
        return payload
    

    @classmethod
    def login(cls, request: Request) -> Response:
        context = {
            'username': request.form['username'], 
            'password': request.form['password']
        }
        authenticator = current_app.cache.config["authenticator"]
        users = current_app.users
        auth = cls(
            **authenticator,
            **users
        ).authenticate(**context)
        
        response = make_response(redirect(url_for("cannettes_bp.admin_lobby")))
        if auth.get("status") == "success":
            response.set_cookie('session', auth["token"])
        return response