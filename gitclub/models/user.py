import json

from loguru import logger
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import Column, Integer, String, Table, Unicode

from ..config import PASSWORD_MIN_LENGTH, PASSWORD_MIN_VARIETY
from ..resources import db
from . import metadata, random_id

crypt_ctx = CryptContext(schemes=['argon2'])


User = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('name', Unicode, nullable=False),
    Column('email', Unicode, nullable=False, unique=True),
    Column('password_hash', String(97), nullable=False),
)


def check_password(password: str) -> str:
    errors = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f'Password length < {PASSWORD_MIN_LENGTH} chars')
    if len(set(password)) < PASSWORD_MIN_VARIETY:
        errors.append(f'Variety < {PASSWORD_MIN_VARIETY} chars')
    if errors:
        raise ValueError(json.dumps(errors))
    return password


class UserInfo(BaseModel):
    id: int
    name: str
    email: EmailStr


class UserInsert(BaseModel):
    name: str
    email: EmailStr
    password: str

    _password = validator('password', allow_reuse=True)(check_password)


class UserPatch(BaseModel):
    name: str | None
    email: EmailStr | None
    password: str | None

    _password = validator('password', allow_reuse=True)(check_password)


async def get_all() -> list[UserInfo]:
    query = User.select()
    logger.debug(query)
    result = await db.fetch_all(query)
    return [UserInfo(**r._mapping) for r in result]


async def get_user_by_email(email: str) -> UserInfo | None:
    query = User.select(User.c.email == email)
    logger.debug(query)
    result = await db.fetch_one(query)
    return UserInfo(**result._mapping) if result else None


async def get_user_by_login(email: str, password: str) -> UserInfo | None:
    query = User.select(User.c.email == email)
    result = await db.fetch_one(query)
    if result and crypt_ctx.verify(password, result['password_hash']):
        return UserInfo(**result._mapping)
    return None


async def get(user_id: int) -> UserInfo | None:
    query = User.select(User.c.id == user_id)
    result = await db.fetch_one(query)
    return UserInfo(**result._mapping) if result else None


async def insert(user: UserInsert) -> int:
    fields = user.dict()
    user_id = fields['id'] = random_id()
    password = fields.pop('password')
    fields['password_hash'] = crypt_ctx.hash(password)
    stmt = User.insert().values(fields)
    await db.execute(stmt)
    return user_id  # noqa: RET504


async def update(user_id: int, patch: UserPatch) -> None:
    fields = patch.dict(exclude_unset=True)
    if 'password' in fields:
        password = fields.pop('password')
        fields['password_hash'] = crypt_ctx.hash(password)
    stmt = User.update().where(User.c.id == user_id).values(**fields)
    await db.execute(stmt)


async def delete(user_id: int) -> None:
    stmt = User.delete().where(User.c.id == user_id)
    await db.execute(stmt)
