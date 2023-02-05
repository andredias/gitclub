from httpx import AsyncClient

from gitclub.schemas.issue import IssueInfo, IssueInsert

from ..utils import logged_session

TestData = dict[str, dict[str, int]]


async def test_list_issues(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    abbey_road = test_dataset['repositories']['abbey_road']
    test_dataset['repositories']['the_white_album']
    beatles = test_dataset['organizations']['beatles']
    acclaim = test_dataset['issues']['acclaim']
    url = '/organizations/{}/repositories/{}/issues'

    # unauthenticated user access
    resp = await client.get(url.format(beatles, abbey_road))
    assert resp.status_code == 401

    await logged_session(client, john)

    # inexistent organization
    resp = await client.get(url.format(0, abbey_road))
    assert resp.status_code == 404

    # inexistent repository
    resp = await client.get(url.format(beatles, 0))
    assert resp.status_code == 404

    # abbey road issues
    resp = await client.get(url.format(beatles, abbey_road))
    assert resp.status_code == 200
    issues = resp.json()
    assert {acclaim} == {i['id'] for i in issues}

    # fulano cannot list issues
    await logged_session(client, fulano)
    resp = await client.get(url.format(beatles, abbey_road))
    assert resp.status_code == 403


async def test_create_issue(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    abbey_road = test_dataset['repositories']['abbey_road']
    url = f'/organizations/{beatles}/repositories/{abbey_road}/issues'

    # unauthenticated user access
    resp = await client.post(url)
    assert resp.status_code == 401

    # john creates an issue
    repo = IssueInsert(
        title='Tralala',
        repository_id=abbey_road,
        creator_id=john,
    )
    await logged_session(client, john)
    resp = await client.post(url, json=repo.dict())
    assert resp.status_code == 201
    assert resp.headers['Location'] == f'{url}/{resp.json()["id"]}'
    assert IssueInfo(**resp.json())

    # fulano is not a member of beatles and cannot create a repository
    await logged_session(client, fulano)
    resp = await client.post(url, json=repo.dict())
    assert resp.status_code == 403


async def test_show_issue(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    abbey_road = test_dataset['repositories']['abbey_road']
    paperwork = test_dataset['repositories']['paperwork']
    beatles = test_dataset['organizations']['beatles']
    acclaim = test_dataset['issues']['acclaim']
    url = '/organizations/{}/repositories/{}/issues/{}'

    # unauthenticated user access
    resp = await client.get(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 401

    # ok
    await logged_session(client, john)
    resp = await client.get(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 200
    assert IssueInfo(**resp.json()).id == acclaim

    # john cannot access a repository that does not belong to beatles
    await logged_session(client, john)
    resp = await client.get(url.format(beatles, paperwork, acclaim))
    assert resp.status_code == 404

    # inexistent organization
    resp = await client.get(url.format(0, abbey_road, acclaim))
    assert resp.status_code == 404

    # inexistent repository
    resp = await client.get(url.format(beatles, 0, acclaim))
    assert resp.status_code == 404

    # fulano is not a member of beatles and cannot access abbey_road
    await logged_session(client, fulano)
    resp = await client.get(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 403


async def test_close_issue(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    abbey_road = test_dataset['repositories']['abbey_road']
    paperwork = test_dataset['repositories']['paperwork']
    beatles = test_dataset['organizations']['beatles']
    monsters = test_dataset['organizations']['monsters']
    acclaim = test_dataset['issues']['acclaim']
    traffic = test_dataset['issues']['traffic']
    url = '/organizations/{}/repositories/{}/issues/{}'

    # unauthenticated user access
    resp = await client.patch(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 401

    # fulano and paul cannot close an issue
    await logged_session(client, fulano)
    resp = await client.patch(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 403
    await logged_session(client, john)
    resp = await client.patch(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 403

    # paul closes the issue
    await logged_session(client, paul)
    resp = await client.patch(url.format(beatles, abbey_road, acclaim))
    assert resp.status_code == 200
    assert IssueInfo(**resp.json()).closed

    # paul cannot close an inexistent issue
    resp = await client.patch(url.format(beatles, abbey_road, 0))
    assert resp.status_code == 404

    # paul cannot close an issue that does not belong to abbey_road
    resp = await client.patch(url.format(monsters, paperwork, traffic))
    assert resp.status_code == 403
