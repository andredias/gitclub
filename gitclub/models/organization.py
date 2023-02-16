from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Table

from ..resources import db
from . import metadata, random_id

Organization = Table(
    'organization',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('name', String, unique=True),
    Column('base_repo_role', String),
    Column('billing_address', String),
)


class OrganizationInsert(BaseModel):
    name: str
    base_repo_role: str
    billing_address: str


class OrganizationInfo(OrganizationInsert):
    id: int


async def insert(organization: OrganizationInsert) -> int:
    fields = organization.dict()
    organization_id = fields['id'] = random_id()
    stmt = Organization.insert().values(fields)
    await db.execute(stmt)
    return organization_id  # noqa: RET504


async def get(id_: int) -> OrganizationInfo | None:
    query = Organization.select(Organization.c.id == id_)
    result = await db.fetch_one(query)
    return OrganizationInfo(**result._mapping) if result else None
