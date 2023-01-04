from sqlalchemy import Column, Integer, String, Table

from . import metadata

Organization = Table(
    'organization',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=False),
    Column('name', String, unique=True),
    Column('base_repo_role', String),
    Column('billing_address', String),
)
