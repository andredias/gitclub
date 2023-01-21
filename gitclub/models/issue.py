from loguru import logger
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table

from ..resources import db
from ..schemas.issue import IssueInsert
from . import metadata, random_id
from .repository import Repository
from .user import User

Issue = Table(
    'issue',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('title', String, nullable=False),
    Column('closed', Boolean, default=False),
    Column('repo_id', ForeignKey(Repository.c.id), nullable=False),
    Column('creator_id', ForeignKey(User.c.id), nullable=False),
)


async def insert(issue: IssueInsert) -> int:
    fields = issue.dict()
    id_ = fields['id'] = random_id()
    stmt = Issue.insert().values(fields)
    logger.debug(stmt)
    await db.execute(stmt)
    return id_  # noqa: RET504
