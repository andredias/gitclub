from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, String, Table

from ..resources import db
from . import metadata
from .organization import Organization, OrganizationInfo
from .user import User

UserOrganization = Table(
    'user_organization',
    metadata,
    Column('user_id', ForeignKey(User.c.id), primary_key=True),
    Column('organization_id', ForeignKey(Organization.c.id), primary_key=True),
    Column('role', String, nullable=False),
)


class UserOrganizationInfo(BaseModel):
    user_id: int
    organization_id: int
    role: str


async def insert(user_organization: UserOrganizationInfo) -> None:
    stmt = UserOrganization.insert().values(user_organization.dict())
    await db.execute(stmt)
    return


async def user_role_in_organization(user_id: int, organization_id: int) -> str | None:
    stmt = UserOrganization.select().where(
        UserOrganization.c.user_id == user_id,
        UserOrganization.c.organization_id == organization_id,
    )
    result = await db.fetch_one(stmt)
    return result['role'] if result else None


async def user_organizations(user_id: int) -> list[OrganizationInfo]:
    query = Organization.select().where(
        Organization.c.id == UserOrganization.c.organization_id,
        UserOrganization.c.user_id == user_id,
    )
    result = await db.fetch_all(query)
    return [OrganizationInfo(**row._mapping) for row in result]
