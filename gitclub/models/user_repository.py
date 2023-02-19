from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, String, Table

from ..resources import db
from . import metadata
from .repository import Repository
from .user import User, UserInfo

UserRepository = Table(
    'user_repository',
    metadata,
    Column('user_id', ForeignKey(User.c.id), primary_key=True),
    Column('repository_id', ForeignKey(Repository.c.id), primary_key=True),
    Column('role', String, nullable=False),
)


class UserRepositoryInfo(BaseModel):
    user_id: int
    repository_id: int
    role: str


class RepositoryMemberInfo(UserInfo):
    role: str


async def insert(user_repository: UserRepositoryInfo) -> None:
    stmt = UserRepository.insert().values(user_repository.dict())
    await db.execute(stmt)
    return


async def get_user_role_in_repository(user_id: int, repository_id: int) -> str | None:
    stmt = UserRepository.select().where(
        UserRepository.c.user_id == user_id,
        UserRepository.c.repository_id == repository_id,
    )
    result = await db.fetch_one(stmt)
    return result['role'] if result else None


async def get_user_repositories(user_id: int) -> list[Repository]:
    stmt = UserRepository.select().where(UserRepository.c.user_id == user_id)
    result = await db.fetch_all(stmt)
    return [Repository(**row._mapping) for row in result]


async def get_repository_non_members(repository_id: int) -> list[UserInfo]:
    query = """
select
    u.id, u.name, u.email
from
    "user" u
left join
    user_repository ur
on
    u.id = ur.user_id and ur.repository_id = :repository_id
where
    ur.user_id is null
"""
    result = await db.fetch_all(query, values={'repository_id': repository_id})
    return [UserInfo(**row._mapping) for row in result]


async def get_repository_members(repository_id: int) -> list[RepositoryMemberInfo]:
    query = """
select
    u.id, u.name, u.email, ur.role
from
    "user" u
inner join
    user_repository ur
on
    u.id = ur.user_id and ur.repository_id = :repository_id
"""
    result = await db.fetch_all(query, values={'repository_id': repository_id})
    return [RepositoryMemberInfo(**row._mapping) for row in result]


async def update_user_repository(user_id: int, repository_id: int, role: str) -> None:
    stmt = (
        UserRepository.update()
        .where(
            UserRepository.c.user_id == user_id,
            UserRepository.c.repository_id == repository_id,
        )
        .values(role=role)
    )
    await db.execute(stmt)
    return


async def delete_user_repository(user_id: int, repository_id: int) -> None:
    stmt = UserRepository.delete().where(
        UserRepository.c.user_id == user_id,
        UserRepository.c.repository_id == repository_id,
    )
    await db.execute(stmt)
    return
