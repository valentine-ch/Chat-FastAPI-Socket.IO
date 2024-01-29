from sqlalchemy.orm import Session
import uuid
import db_models


def create_user(db: Session, login: str, hashed_password: str, name: str, email: str | None):
    user_id = uuid.uuid4()
    user = db_models.User(user_id=user_id, name=name, is_guest=False)
    account_data = db_models.AccountData(user_id=user_id, login=login, hashed_password=hashed_password, email=email)
    user.account_data = account_data

    db.add(user)
    db.commit()
    return user_id


def create_guest_user(db: Session, name: str):
    user_id = uuid.uuid4()
    guest = db_models.User(user_id=user_id, name=name, is_guest=True)

    db.add(guest)
    db.commit()
    return user_id


def get_user_by_id(db: Session, user_id: str):
    return db.query(db_models.User).filter(db_models.User.user_id == uuid.UUID(user_id)).first()


def get_user_by_login(db: Session, login: str):
    return db.query(db_models.User).join(db_models.AccountData).filter(db_models.AccountData.login == login).first()


def get_user_by_email(db: Session, email: str):
    return db.query(db_models.User).join(db_models.AccountData).filter(db_models.AccountData.email == email).first()


def update_username(db: Session, user_id: str, new_name: str):
    user = get_user_by_id(db, user_id)
    user.name = new_name
    db.commit()
    return user
