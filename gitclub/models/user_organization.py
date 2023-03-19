from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, String, Table, and_, join

from ..resources import db
from . import metadata
from .organization import Organization, OrganizationInfo
from .user import User, UserInfo

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


class OrganizationMemberInfo(UserInfo):
    role: str


async def insert(user_organization: UserOrganizationInfo) -> None:
    stmt = UserOrganization.insert().values(user_organization.dict())
    await db.execute(stmt)


async def get_user_role_in_organization(user_id: int, organization_id: int) -> str | None:
    stmt = UserOrganization.select().where(
        UserOrganization.c.user_id == user_id,
        UserOrganization.c.organization_id == organization_id,
    )
    result = await db.fetch_one(stmt)
    return result['role'] if result else None


async def get_user_organizations(user_id: int) -> list[OrganizationInfo]:
    query = Organization.select().where(
        Organization.c.id == UserOrganization.c.organization_id,
        UserOrganization.c.user_id == user_id,
    )
    result = await db.fetch_all(query)
    return [OrganizationInfo(**row._mapping) for row in result]


async def get_organization_members(organization_id: int) -> list[OrganizationMemberInfo]:
    query = """
select
    u.id, u.name, u.email, uo.role
from
    "user" u
inner join
    user_organization uo
on
    u.id = uo.user_id and uo.organization_id = :organization_id
"""
    result = await db.fetch_all(query, values={'organization_id': organization_id})
    return [OrganizationMemberInfo(**row._mapping) for row in result]


async def get_organization_non_members(organization_id: int) -> list[UserInfo]:
    left_join = join(
        User,
        UserOrganization,
        and_(
            User.c.id == UserOrganization.c.user_id,
            UserOrganization.c.organization_id == organization_id,
        ),
        isouter=True,
    )
    query = (
        User.select()
        .select_from(left_join)
        .where(
            UserOrganization.c.organization_id == None,  # noqa: E711
        )
    )
    result = await db.fetch_all(query)
    return [UserInfo(**row._mapping) for row in result]


async def update_user_organization(user_id: int, organization_id: int, role: str) -> None:
    stmt = (
        UserOrganization.update()
        .where(
            UserOrganization.c.user_id == user_id,
            UserOrganization.c.organization_id == organization_id,
        )
        .values(role=role)
    )
    await db.execute(stmt)


async def delete_user_organization(user_id: int, organization_id: int) -> None:
    stmt = UserOrganization.delete().where(
        UserOrganization.c.user_id == user_id,
        UserOrganization.c.organization_id == organization_id,
    )
    await db.execute(stmt)
