from sqlalchemy import Column, ForeignKey, String, Table

from ..resources import db
from ..schemas.user_organization import UserOrganizationInfo
from . import metadata
from .organization import Organization
from .user import User

UserOrganization = Table(
    'user_organization',
    metadata,
    Column('user_id', ForeignKey(User.c.id), primary_key=True),
    Column('organization_id', ForeignKey(Organization.c.id), primary_key=True),
    Column('role', String, nullable=False),
)


async def insert(user_organization: UserOrganizationInfo) -> None:
    stmt = UserOrganization.insert().values(user_organization.dict())
    await db.execute(stmt)
    return
