from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table

from . import metadata
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
