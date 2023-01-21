from sqlalchemy import Column, ForeignKey, String, Table

from ..resources import db
from ..schemas.user_repository import UserRepositoryInfo
from . import metadata
from .repository import Repository
from .user import User

UserRepository = Table(
    'user_repository',
    metadata,
    Column('user_id', ForeignKey(User.c.id), primary_key=True),
    Column('repository_id', ForeignKey(Repository.c.id), primary_key=True),
    Column('role', String, nullable=False),
)


async def insert(user_repository: UserRepositoryInfo) -> None:
    stmt = UserRepository.insert().values(user_repository.dict())
    await db.execute(stmt)
    return
