from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint

from . import metadata
from .organization import Organization

Repository = Table(
    'repository',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('name', String, unique=True),
    Column('organization_id', ForeignKey(Organization.c.id), nullable=False),
    UniqueConstraint('name', 'organization_id'),
)
