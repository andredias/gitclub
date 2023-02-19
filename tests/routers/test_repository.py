from fastapi import status
from httpx import AsyncClient

from gitclub.models.repository import RepositoryInfo, RepositoryInsert

from ..utils import logged_session

TestData = dict[str, dict[str, int]]


async def test_list_repositories(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    abbey_road = test_dataset['repositories']['abbey_road']
    the_white_album = test_dataset['repositories']['the_white_album']
    beatles = test_dataset['organizations']['beatles']
    url = f'/organizations/{beatles}/repositories'

    # unauthenticated user access
    resp = await client.get(url)
    assert resp.status_code == 401

    # beatles's repositories
    await logged_session(client, john)
    resp = await client.get(url)
    assert resp.status_code == 200
    repositories = resp.json()
    assert len(repositories) == 2
    assert {abbey_road, the_white_album} == {r['id'] for r in repositories}

    # fulano is not a member of beatles and cannot list repositories
    await logged_session(client, fulano)
    resp = await client.get(url)
    assert resp.status_code == 403


async def test_create_repository(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    url = f'/organizations/{beatles}/repositories'

    # unauthenticated user access
    resp = await client.post(url)
    assert resp.status_code == 401

    # john creates a repository
    repo = RepositoryInsert(
        name='Mutantes', base_repo_role='reader', billing_address='Rua dos Bobos, 0'
    )
    await logged_session(client, john)
    resp = await client.post(url, json=repo.dict())
    assert resp.status_code == 201
    assert RepositoryInfo(**resp.json())

    # fulano is not a member of beatles and cannot create a repository
    await logged_session(client, fulano)
    resp = await client.post(url, json=repo.dict())
    assert resp.status_code == 403


async def test_show_repository(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    abbey_road = test_dataset['repositories']['abbey_road']
    paperwork = test_dataset['repositories']['paperwork']
    beatles = test_dataset['organizations']['beatles']
    url = '/organizations/{}/repositories/{}'

    # unauthenticated user access
    resp = await client.get(url.format(beatles, abbey_road))
    assert resp.status_code == 401

    # ok
    await logged_session(client, john)
    resp = await client.get(url.format(beatles, abbey_road))
    assert resp.status_code == 200
    assert RepositoryInfo(**resp.json()).id == abbey_road

    # john cannot access a repository that does not belong to beatles
    await logged_session(client, john)
    resp = await client.get(url.format(beatles, paperwork))
    assert resp.status_code == 404

    # inexistent organization
    resp = await client.get(url.format(0, abbey_road))
    assert resp.status_code == 404

    # inexistent repository
    resp = await client.get(url.format(beatles, 0))
    assert resp.status_code == 404

    # fulano is not a member of beatles and cannot access abbey_road
    await logged_session(client, fulano)
    resp = await client.get(url.format(beatles, abbey_road))
    assert resp.status_code == 403


async def test_list_members(test_dataset: TestData, client: AsyncClient) -> None:
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    abbey_road = test_dataset['repositories']['abbey_road']
    url = f'/organizations/{beatles}/repositories/{abbey_road}/members'

    # unauthenticated user access
    resp = await client.get(url)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # fulano is not a member of beatles and cannot list members
    await logged_session(client, fulano)
    resp = await client.get(url)
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # abbey_road's members
    await logged_session(client, paul)
    resp = await client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    members = resp.json()
    assert len(members) == 3
    assert {'john', 'paul', 'mike'} == {m['name'] for m in members}


async def test_list_non_members(test_dataset: TestData, client: AsyncClient) -> None:
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    abbey_road = test_dataset['repositories']['abbey_road']
    url = f'/organizations/{beatles}/repositories/{abbey_road}/non-members'

    # unauthenticated user access
    resp = await client.get(url)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # fulano is not a member of beatles and cannot list non members
    await logged_session(client, fulano)
    resp = await client.get(url)
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # beatles's non members
    await logged_session(client, paul)
    resp = await client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    non_members = resp.json()
    assert len(non_members) == 5
    assert {'fulano', 'sully', 'randall', 'admin', 'ringo'} == {m['name'] for m in non_members}


async def test_add_member(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    abbey_road = test_dataset['repositories']['abbey_road']
    url = f'/organizations/{beatles}/repositories/{abbey_road}/members'

    # unauthenticated user access
    resp = await client.post(url, json={'user_id': fulano, 'role': 'maintainer'})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # john is not authorized to add members
    await logged_session(client, john)
    resp = await client.post(url, json={'user_id': fulano, 'role': 'maintainer'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # paul tries to add an inexistent user
    await logged_session(client, paul)
    resp = await client.post(url, json={'user_id': -1, 'role': 'maintainer'})
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    # john is already a member
    resp = await client.post(url, json={'user_id': john, 'role': 'maintainer'})
    assert resp.status_code == status.HTTP_409_CONFLICT

    # invalid role
    resp = await client.post(url, json={'user_id': fulano, 'role': 'foobar'})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # paul adds fulano as a member
    resp = await client.post(url, json={'user_id': fulano, 'role': 'admin'})
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data['user_id'] == fulano
    assert data['role'] == 'admin'
    assert data['repository_id'] == abbey_road
    assert resp.headers['Location'] == (
        f'/organizations/{beatles}/repositories/{abbey_road}/members/{fulano}'
    )


async def test_update_member_role(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    abbey_road = test_dataset['repositories']['abbey_road']
    url = f'/organizations/{beatles}/repositories/{abbey_road}/members/{fulano}'

    # unauthenticated user access
    resp = await client.put(url, json={'role': 'maintainer'})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # john is not authorized to update members
    await logged_session(client, john)
    resp = await client.put(url, json={'role': 'maintainer'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # fulano is not a member of the repository
    await logged_session(client, paul)
    resp = await client.put(url, json={'role': 'maintainer'})
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    # invalid role
    url = f'/organizations/{beatles}/repositories/{abbey_road}/members/{john}'
    resp = await client.put(url, json={'role': 'foobar'})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # paul updates fulano's role
    resp = await client.put(url, json={'role': 'maintainer'})
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data['user_id'] == john
    assert data['role'] == 'maintainer'
    assert data['repository_id'] == abbey_road

    # paul updates john's role to same role
    resp = await client.put(url, json={'role': 'maintainer'})
    assert resp.status_code == status.HTTP_200_OK


async def test_remove_member(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    ringo = test_dataset['users']['ringo']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    abbey_road = test_dataset['repositories']['abbey_road']
    url = f'/organizations/{beatles}/repositories/{abbey_road}/members/{{}}'

    # unauthenticated user access
    resp = await client.delete(url.format(fulano))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # john is not authorized to remove members
    await logged_session(client, john)
    resp = await client.delete(url.format(paul))
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # john should be able to remove himself
    resp = await client.delete(url.format(john))
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # paul tries to remove fulano, but he is not a member
    await logged_session(client, paul)
    resp = await client.delete(url.format(fulano))
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # paul removes ringo
    resp = await client.delete(url.format(ringo))
    assert resp.status_code == status.HTTP_204_NO_CONTENT
