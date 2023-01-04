from sqlalchemy import Column, ForeignKey, String, Table

from . import metadata
from .repository import Repository
from .user import User

UserOrganization = Table(
    'user_repository',
    metadata,
    Column('user_id', ForeignKey(User.c.id), primary_key=True),
    Column('repository_id', ForeignKey(Repository.c.id), primary_key=True),
    Column('role', String, nullable=False),
)
