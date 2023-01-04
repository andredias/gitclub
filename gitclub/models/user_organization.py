from sqlalchemy import Column, ForeignKey, String, Table

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
