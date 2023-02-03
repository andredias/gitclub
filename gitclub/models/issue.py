from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table

from ..resources import db
from ..schemas.issue import IssueInfo, IssueInsert
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


async def get(id: int) -> IssueInfo | None:
    query = Issue.select(Issue.c.id == id)
    result = await db.fetch_one(query)
    return IssueInfo(**result._mapping) if result else None
