from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uuid
from pydantic import ValidationError
import time
import schemas
from auth import users, generate_token, validate_token


app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi")
sid_user_data = dict()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping():
    return "pong"


@app.post("/create_user")
async def create_user(body: schemas.Registration):
    user_id = str(uuid.uuid4())
    token = generate_token(user_id)
    users[user_id] = body.name
    return {"user_id": user_id, "token": token}


@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token")
    if token is None:
        return False
    user_id = validate_token(token)
    if user_id is None:
        return False
    sid_user_data[sid] = user_id


@sio.event
async def disconnect(sid):
    sid_user_data.pop(sid, None)


@sio.event
async def message(sid, data):
    try:
        validated_data = schemas.Message(**data)
        user_id = sid_user_data[sid]
        await sio.emit("message", {
            "user": {
                "id": user_id,
                "name": users[user_id]
            },
            "text": validated_data.text,
            "room": validated_data.room,
            "timestamp": int(time.time() * 1000)
        })
    except ValidationError:
        pass


@sio.event
async def start_typing(sid, data):
    try:
        room = schemas.Typing(**data).room
        user_id = sid_user_data[sid]
        await sio.emit("start_typing", {
            "user": {
                "id": user_id,
                "name": users[user_id]
            },
            "room": room
        })
    except ValidationError:
        pass


@sio.event
async def stop_typing(sid, data):
    try:
        room = schemas.Typing(**data).room
        user_id = sid_user_data[sid]
        await sio.emit("stop_typing", {
            "user": {
                "id": user_id,
                "name": users[user_id]
            },
            "room": room
        })
    except ValidationError:
        pass


app.mount("/socket.io", socketio.ASGIApp(sio))
