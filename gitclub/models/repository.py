from loguru import logger
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint

from ..resources import db
from ..schemas.repository import RepositoryInsert
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
    logger.debug(stmt)
    await db.execute(stmt)
    return id_  # noqa: RET504
