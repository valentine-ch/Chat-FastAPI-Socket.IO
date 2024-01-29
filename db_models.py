from sqlalchemy import Column, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID, primary_key=True)
    is_guest = Column(Boolean, nullable=False)
    name = Column(String, nullable=False)
    account_data = relationship("AccountData", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @validates("is_guest", "account_data")
    def validate_user(self, key, value):
        if key == "is_guest":
            if value and self.account_data:
                raise ValueError("Users with account data cannot be guests")
        elif key == "account_data":
            if value and self.is_guest:
                raise ValueError("Guest users cannot have account data")
            if not value and not self.is_guest:
                raise ValueError("Non-guest users must have account data")
        return value


class AccountData(Base):
    __tablename__ = "account_data"

    user_id = Column(UUID, ForeignKey("users.user_id"), primary_key=True)
    login = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    user = relationship("User", back_populates="account_data")
