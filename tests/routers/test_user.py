from httpx import AsyncClient

from gitclub.models.user import UserInfo

from ..utils import logged_session

TestData = dict[str, dict[str, int]]


async def test_get_user(test_dataset: TestData, client: AsyncClient) -> None:
    url = '/users/{}'
    john = test_dataset['users']['john']
    fulano = -1

    # unauthenticated user
    resp = await client.get(url.format(john))
    assert resp.status_code == 401

    # tries to get inexistent user
    await logged_session(client, fulano)
    resp = await client.get(url.format(fulano))
    assert resp.status_code == 404

    # tries to get an existing user
    await logged_session(client, john)
    resp = await client.get(url.format(john))
    assert resp.status_code == 200
    assert UserInfo(**resp.json()).id == john
