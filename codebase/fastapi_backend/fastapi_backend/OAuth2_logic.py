from fastapi import HTTPException, Depends, status
from sqlmodel import Session, select
from .models import User
from .db import engine
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


ALGORITHM = "HS256"
SECRET_KEY = "My secure key"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(subject: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(access_token: str):
    decoded_jwt = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
    return decoded_jwt


def authenticate_user(username: str,
                      password: str):
    with Session(engine) as session:
        statement_user = select(User).where(User.username == username)
        user_object = session.exec(statement=statement_user).first()
        if username != user_object.username:
            return False
        if not user_object.verify_password(password=password):
            return False
        return user_object
    

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user_token_data = decode_access_token(access_token=token)
        with Session(engine) as session:
            statement = select(User).where(User.username == user_token_data['sub'])
            user_object = session.exec(statement).first()
            if not user_object:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return User.model_validate(user_object)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )