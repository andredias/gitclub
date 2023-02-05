from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table

from ..resources import db
from ..schemas.issue import IssueInfo, IssueInsert, IssuePatch
from . import metadata, random_id
from .repository import Repository
from .user import User

Issue = Table(
    'issue',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('title', String, nullable=False),
    Column('closed', Boolean, default=False),
    Column('repository_id', ForeignKey(Repository.c.id), nullable=False),
    Column('creator_id', ForeignKey(User.c.id), nullable=False),
)


async def insert(issue: IssueInsert) -> int:
    fields = issue.dict()
    id_ = fields['id'] = random_id()
    stmt = Issue.insert().values(fields)
    await db.execute(stmt)
    return id_  # noqa: RET504


async def get(
    issue_id: int, repository_id: int | None = None, organization_id: int | None = None
) -> IssueInfo | None:
    query = Issue.select(Issue.c.id == issue_id)
    if repository_id is not None:
        query = query.where(Issue.c.repository_id == repository_id)
        if organization_id is not None:
            query = query.where(Repository.c.organization_id == organization_id)
    result = await db.fetch_one(query)
    return IssueInfo(**result._mapping) if result else None


async def get_repository_issues(repository_id: int) -> list[IssueInfo]:
    query = Issue.select(Issue.c.repository_id == repository_id)
    results = await db.fetch_all(query)
    return [IssueInfo(**result._mapping) for result in results]


async def update(issue_id: int, patch: IssuePatch) -> None:
    fields = patch.dict(exclude_unset=True)
    stmt = Issue.update().where(Issue.c.id == issue_id).values(**fields)
    await db.execute(stmt)
    return
