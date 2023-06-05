from datetime import timedelta
from typing import Union

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from core import schemas, crud
from core.auth import authenticate_user, create_access_token
from core.database import get_db
from settings import ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/")
def base():
    return {"hello": "Hello world."}


@app.get("/items/{item_id}/{item_name}")
def read_item(item_id: int, item_name: str, q: Union[str, None] = None):
    return {
        "item_id": item_id,
        "name": item_name,
        "q": q
    }


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}


@app.post("/users/register/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/users/token", response_model=schemas.Token)
def login_for_access_token(user: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user.email, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}