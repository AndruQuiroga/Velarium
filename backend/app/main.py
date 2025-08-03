import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from .auth import authenticate
from .routers import servers

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "change-me"))


class LoginPayload(BaseModel):
    username: str
    password: str
    use_token: bool = False


@app.post("/login")
def login(payload: LoginPayload, request: Request):
    return authenticate(request, payload.username, payload.password, payload.use_token)


app.include_router(servers.router)
