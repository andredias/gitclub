from httpx import AsyncClient

from gitclub.schemas.repository import RepositoryInfo, RepositoryInsert

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
