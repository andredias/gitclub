from httpx import AsyncClient

from gitclub.models.user import UserInfo

from ..utils import logged_session

TestData = dict[str, dict[str, int]]


async def test_get_user(test_dataset: TestData, client: AsyncClient) -> None:
    url = '/users/{}'
    john = test_dataset['users']['john']
    mike = test_dataset['users']['mike']
    beltrano = -1

    # unauthenticated user
    resp = await client.get(url.format(john))
    assert resp.status_code == 401

    # tries to get inexistent user
    await logged_session(client, john)
    resp = await client.get(url.format(beltrano))
    assert resp.status_code == 404

    # tries to get an existing user
    await logged_session(client, john)
    resp = await client.get(url.format(mike))
    assert resp.status_code == 200
    assert UserInfo(**resp.json()).id == mike


async def test_get_user_repositories(test_dataset: TestData, client: AsyncClient) -> None:
    url = '/users/{}/repositories'
    john = test_dataset['users']['john']
    mike = test_dataset['users']['mike']
    fulano = test_dataset['users']['fulano']
    beltrano = -1
    abbey_road = test_dataset['repositories']['abbey_road']
    paperwork = test_dataset['repositories']['paperwork']

    # unauthenticated user
    resp = await client.get(url.format(john))
    assert resp.status_code == 401

    # tries to get inexistent user
    await logged_session(client, fulano)
    resp = await client.get(url.format(beltrano))
    assert resp.status_code == 404

    # fulano gets mike's repositories
    resp = await client.get(url.format(mike))
    assert resp.status_code == 200
    assert resp.json() == []  # fulano has no access to repositories or organizations

    # john gets mike's repositories
    await logged_session(client, john)
    resp = await client.get(url.format(mike))
    assert resp.status_code == 200
    repositories = resp.json()
    # john can only see part of mike's repositories that he has access to
    assert [r['id'] for r in repositories] == [abbey_road]

    # mike gets his own repositories
    await logged_session(client, mike)
    resp = await client.get(url.format(mike))
    assert resp.status_code == 200
    repositories = resp.json()
    assert {r['id'] for r in repositories} == {paperwork, abbey_road}
