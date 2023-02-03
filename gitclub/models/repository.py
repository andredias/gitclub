from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint

from ..resources import db
from ..schemas.repository import RepositoryInfo, RepositoryInsert
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


async def insert(repository: RepositoryInsert) -> int:
    fields = repository.dict()
    id_ = fields['id'] = random_id()
    stmt = Repository.insert().values(fields)
    await db.execute(stmt)
    return id_  # noqa: RET504


async def get(id: int) -> RepositoryInfo | None:
    query = Repository.select(Repository.c.id == id)
    result = await db.fetch_one(query)
    return RepositoryInfo(**result._mapping) if result else None
