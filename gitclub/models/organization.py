from loguru import logger
from sqlalchemy import Column, Integer, String, Table

from ..resources import db
from ..schemas.organization import OrganizationInsert
from . import metadata, random_id

Organization = Table(
    'organization',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('name', String, unique=True),
    Column('base_repo_role', String),
    Column('billing_address', String),
)


async def insert(organization: OrganizationInsert) -> int:
    fields = organization.dict()
    id_ = fields['id'] = random_id()
    stmt = Organization.insert().values(fields)
    logger.debug(stmt)
    await db.execute(stmt)
    return id_  # noqa: RET504
