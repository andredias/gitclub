from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint, bindparam, text

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


async def get_allowed_repositories(
    user_id: int,
    org_roles: Sequence[str],
    repo_roles: Sequence[str],
) -> list[RepositoryInfo]:
    query = text(
        """\
    select
        r.id, r.name, r.organization_id
    from
        repository r
    inner join
        user_repository ur
    on
        r.id = ur.repository_id
        and ur.user_id = :user_id
        and ur.role in :repo_roles
union
    select
        r.id, r.name, r.organization_id
    from
        repository r
    inner join
        user_organization uo
    on
        r.organization_id = uo.organization_id
        and uo.user_id = :user_id
        and uo.role in :org_roles"""
    ).bindparams(
        bindparam('repo_roles', value=repo_roles, expanding=True),
        bindparam('org_roles', value=org_roles, expanding=True),
        user_id=user_id,
    )
    result = await db.fetch_all(query)
    return [RepositoryInfo(**row._mapping) for row in result]


async def get_organization_repositories(organization_id: int) -> list[RepositoryInfo]:
    query = Repository.select(Repository.c.organization_id == organization_id)
    result = await db.fetch_all(query)
    return [RepositoryInfo(**row._mapping) for row in result]
