from fastapi import FastAPI
from pytest import fixture

from gitclub.models import user

Users = list[user.UserInfo]


@fixture(scope='module')
async def users(session_app: FastAPI) -> Users:
    return await user.get_all()


async def test_get_user(users: Users) -> None:
    all_users = await user.get_all()
    assert all_users == users


async def test_get_user_by_id(users: Users) -> None:
    # ok
    user_info = await user.get(users[0].id)
    assert user_info == users[0]

    # inexistent user
    user_info = await user.get(-1)
    assert user_info is None


async def test_get_user_by_email(users: Users) -> None:
    # ok
    user_info = await user.get_user_by_email(users[0].email)
    assert user_info == users[0]

    # inexistent user
    user_info = await user.get_user_by_email('valid@email.com')
    assert user_info is None


async def test_get_user_by_login(users: Users) -> None:
    # ok
    email = password = users[0].email
    user_info = await user.get_user_by_login(email, password)
    assert user_info == users[0]

    # incorrect email + password
    user_info = await user.get_user_by_login(email, 'abcdefgh1234567890')
    assert user_info is None
