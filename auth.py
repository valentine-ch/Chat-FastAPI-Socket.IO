from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
import jwt
import secrets
import re


security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ph = PasswordHasher()
secret_key = secrets.token_hex(256)


def generate_token(user_id):
    token = jwt.encode({'user': user_id}, secret_key, algorithm='HS256')
    return token


def validate_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload['user']
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def validata_token_in_header(token: str = Depends(oauth2_scheme)):
    user_id = validate_token(token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid token")
    return user_id


def validate_login(login: str):
    if not (2 <= len(login) <= 16):
        raise HTTPException(status_code=400, detail="Username must be 2 to 16 characters long")

    if not re.match(r"^[a-zA-Z0-9]+$", login):
        raise HTTPException(status_code=400, detail="Username can have only English letters and numbers")


def validate_password(password: str):
    if not (8 <= len(password) <= 32):
        raise HTTPException(status_code=400, detail="Password must be 8 to 32 characters long")

    if not re.match(r"^[!-~]+$", password):
        raise HTTPException(status_code=400, detail="Password can have only ASCII symbols excluding whitespace")


def verify_password(hashed_password, password):
    try:
        if ph.verify(hashed_password, password):
            return True
        else:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
    except Argon2Error:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
