
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
        options: Dict[str, Any] = {},
        users: Optional[Dict[str, Any]]= None,
        **kwargs
        ) -> None:
        self.secret_key = secret_key
        self.salt = salt
        self.options = options
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
        return {"status": "success", "token": token}
        
    def load_users(self, users_path: str) -> Dict[str, Any]:
        with open(users_path, 'r') as f:
            users = load(f, SafeLoader)
        return users
        
    def verify_access(self, cookie: str):
        token = cookie.split(" ")[1]
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
        auth = cls(**authenticator,**users)
        auth_request = auth.authenticate(**context)
        response = make_response(redirect(url_for("scannettes_bp.login")))
        if auth_request.get("status") == "success":
            response = make_response(redirect(url_for("scannettes_bp.admin_lobby")))
            response.set_cookie('Authorization', f"Bearer {auth_request['token']}",**auth.options)
        return response