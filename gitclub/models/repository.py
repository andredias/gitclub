from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint

from ..resources import db
from . import metadata, random_id
from .organization import Organization

Repository = Table(
    'repository',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('name', String),
    Column('organization_id', ForeignKey(Organization.c.id), nullable=False),
    UniqueConstraint('name', 'organization_id'),
)


class RepositoryInsert(BaseModel):
    name: str


class RepositoryInsert2(RepositoryInsert):
    organization_id: int


class RepositoryInfo(RepositoryInsert2):
    id: int


async def insert(repository: RepositoryInsert) -> int:
    fields = repository.dict()
    id_ = fields['id'] = random_id()
    stmt = Repository.insert().values(fields)
    await db.execute(stmt)
    return id_  # noqa: RET504


async def get(id: int, organization_id: int | None = None) -> RepositoryInfo | None:
    query = Repository.select(Repository.c.id == id)
    if organization_id is not None:
        query = query.where(Repository.c.organization_id == organization_id)
    result = await db.fetch_one(query)
    return RepositoryInfo(**result._mapping) if result else None


async def get_organization_repositories(organization_id: int) -> list[RepositoryInfo]:
    query = Repository.select(Repository.c.organization_id == organization_id)
    result = await db.fetch_all(query)
    return [RepositoryInfo(**row._mapping) for row in result]
