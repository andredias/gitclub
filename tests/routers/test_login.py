from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from pytest import mark

from gitclub.models import user

TestData = dict[str, dict[str, int]]


async def test_successful_login(test_dataset: TestData, client: AsyncClient) -> None:
    john = await user.get(test_dataset['users']['john'])
    assert john
    resp = await client.post('/login', json={'email': john.email, 'password': john.email})
    assert resp.status_code == 200
    assert resp.headers.get('x-csrf-token')
    assert len(resp.cookies) == 1 and 'session_id' in resp.cookies
    session_id_props = set(resp.headers.get_list('set-cookie')[0].split('; '))
    assert {'HttpOnly', 'Secure', 'SameSite=lax'} <= session_id_props


@patch('gitclub.routers.login.delete_session')
async def test_successful_login_with_session_id(
    delete_session: AsyncMock, test_dataset: TestData, client: AsyncClient
) -> None:
    """
    A user log in with an existing session_id which can be from the same user
    or not
    """
    session_id = 'abcd1234'
    cookies = {'session_id': session_id}
    john = await user.get(test_dataset['users']['john'])
    assert john
    resp = await client.post(
        '/login', json={'email': john.email, 'password': john.email}, cookies=cookies
    )
    assert resp.status_code == 200
    assert resp.cookies['session_id'] != session_id
    assert resp.headers.get('x-csrf-token')
    delete_session.assert_awaited_once_with(session_id)


async def test_unsuccessful_login(client: AsyncClient) -> None:
    email = 'sicrano@email.com'
    password = '12345'
    resp = await client.post('/login', json={'email': email, 'password': password})
    assert resp.status_code == 404
    assert not bool(resp.headers.get('set-cookie'))
    assert resp.headers.get('x-csrf-token') is None


@patch('gitclub.routers.login.delete_session')
@mark.parametrize('cookies,called', [({}, False), ({'session_id': 'abcd1234'}, True)])
async def test_logout(
    delete_session: AsyncMock,
    cookies: dict[str, str],
    called: bool,
    client: AsyncClient,
) -> None:
    resp = await client.post('/logout', cookies=cookies)
    cookies_headers = resp.headers.get('set-cookie')

    assert resp.status_code == 204
    assert 'session_id=""' in cookies_headers
    assert 'Max-Age=0' in cookies_headers
    assert delete_session.called is called
