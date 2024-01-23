import jwt
import secrets


secret_key = secrets.token_hex(256)
users = dict()


def generate_token(user_id):
    token = jwt.encode({'user': user_id}, secret_key, algorithm='HS256')
    return token


def validate_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload['user']
        if user_id not in users:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
