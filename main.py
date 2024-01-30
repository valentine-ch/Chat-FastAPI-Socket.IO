from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import socketio
from pydantic import ValidationError
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import schemas
from database import init_db, get_db, db_session
import crud
from auth import (
    generate_token, validate_token, validata_token_in_header, ph, validate_login, validate_password, verify_password,
    validate_name
)


init_db()
app = FastAPI()
security = HTTPBasic()
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


@app.post("/create_account")
async def register(body: schemas.Registration, db: Session = Depends(get_db)):
    validate_login(body.login)
    validate_password(body.password)
    validate_name(body.name)
    hashed_password = ph.hash(body.password)
    try:
        if crud.get_user_by_login(db, body.login):
            raise HTTPException(status_code=400, detail="This login is taken")
        if body.email and crud.get_user_by_email(db, body.email):
            raise HTTPException(status_code=400, detail="Account with this email already exists")
        user_id_str = str(crud.create_user(db=db, login=body.login, hashed_password=hashed_password,
                                           name=body.name, email=body.email))
        token = generate_token(user_id_str)
        return {"user_id": user_id_str, "token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Unexpected database error")


@app.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        user_login = credentials.username
        password = credentials.password
        user = crud.get_user_by_login(db, user_login)
        if user is None:
            raise HTTPException(status_code=400, detail="Account with this login does not exist")
        verify_password(user.account_data.hashed_password, password)
        user_id_str = str(user.user_id)
        token = generate_token(user_id_str)
        return {"user_id": user_id_str, "token": token}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Unexpected database error")


@app.post("/guest_login")
async def create_user(body: schemas.GuestLogin, db: Session = Depends(get_db)):
    validate_name(body.name)
    try:
        user_id_str = str(crud.create_guest_user(db, body.name))
        token = generate_token(user_id_str)
        return {"user_id": user_id_str, "token": token}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Unexpected database error")


@app.post("/change_name")
async def change_name(body: schemas.UpdateName, user_id: str = Depends(validata_token_in_header),
                      db: Session = Depends(get_db)):
    validate_name(body.new_name)
    try:
        user = crud.update_username(db, user_id, body.new_name)
        return {"status": "success", "new_name": user.name}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Unexpected database error")


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
    with db_session as db:
        try:
            validated_data = schemas.Message(**data)
            user_id = sid_user_data[sid]
            name = crud.get_user_by_id(db, user_id).name
            await sio.emit("message", {
                "user": {
                    "id": user_id,
                    "name": name
                },
                "text": validated_data.text,
                "room": validated_data.room,
                "timestamp": int(time.time() * 1000)
            })
        except ValidationError:
            pass


@sio.event
async def start_typing(sid, data):
    with db_session as db:
        try:
            room = schemas.Typing(**data).room
            user_id = sid_user_data[sid]
            name = crud.get_user_by_id(db, user_id).name
            await sio.emit("start_typing", {
                "user": {
                    "id": user_id,
                    "name": name
                },
                "room": room
            })
        except ValidationError:
            pass


@sio.event
async def stop_typing(sid, data):
    with db_session as db:
        try:
            room = schemas.Typing(**data).room
            user_id = sid_user_data[sid]
            name = crud.get_user_by_id(db, user_id).name
            await sio.emit("stop_typing", {
                "user": {
                    "id": user_id,
                    "name": name
                },
                "room": room
            })
        except ValidationError:
            pass


app.mount("/socket.io", socketio.ASGIApp(sio))
