import os
from pathlib import Path
from subprocess import check_call
from typing import AsyncIterable

from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from pytest import fixture

os.environ['ENV'] = 'testing'

from gitclub.main import app as _app  # noqa: E402
from gitclub.resources import db  # noqa: E402


@fixture(scope='session')
async def init_test_db() -> None:
    """
    Initialize the database.
    """
    from databases import Database
    from sqlalchemy.engine.url import make_url

    from gitclub import config
    from gitclub.resources import connect_database

    url = make_url(config.DATABASE_URL).set(database='postgres')
    db = Database(str(url))
    await connect_database(db)

    try:
        stmt = f"select 1 from pg_database where datname='{config.DB_NAME}'"
        db_exists = await db.execute(stmt)
        if db_exists and os.getenv('RECREATE_DB', 0):
            stmt = f'drop database {config.DB_NAME}'
            await db.execute(stmt)
            db_exists = False
        if not db_exists:
            stmt = f'create database {config.DB_NAME}'
            await db.execute(stmt)
    finally:
        await db.disconnect()
    check_call('alembic upgrade head'.split(), cwd=Path(__file__).parent.parent)
    return


@fixture(scope='session')
async def session_app(init_test_db: None) -> AsyncIterable[FastAPI]:
    """
    Create a FastAPI instance.
    """
    async with LifespanManager(_app):
        yield _app


@fixture
async def app(session_app: FastAPI) -> AsyncIterable[FastAPI]:
    async with db.transaction(force_rollback=True):
        yield session_app


@fixture
async def client(app: FastAPI) -> AsyncIterable[AsyncClient]:
    async with AsyncClient(app=app, base_url='http://testserver') as client:
        yield client


@fixture(scope='session')
async def test_dataset(session_app: FastAPI) -> dict[str, dict[str, int]]:
    """
    Populate the database with users, organizations, repositories and relationships.
    The dataset is common to all tests because it is created before a transaction is
    wrapped around each test.
    """
    from gitclub.initial_data import load_test_dataset

    return await load_test_dataset()


@fixture(scope='session', autouse=True)
def faker_seed() -> int:
    return 0
