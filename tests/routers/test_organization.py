from httpx import AsyncClient

from gitclub.schemas.organization import OrganizationInsert

from ..utils import logged_session

TestData = dict[str, dict[str, int]]


async def test_list_organizations(test_dataset: TestData, client: AsyncClient) -> None:
    url = '/organizations'
    john = test_dataset['users']['john']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']

    # unauthenticated user access
    resp = await client.get(url)
    assert resp.status_code == 401

    # john's organizations
    await logged_session(client, john)
    resp = await client.get(url)
    assert resp.status_code == 200
    orgs = resp.json()
    assert len(orgs) == 1
    assert orgs[0]['id'] == beatles

    # fulano is not a member of any organization
    await logged_session(client, fulano)
    resp = await client.get(url)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


async def test_create_organization(test_dataset: TestData, client: AsyncClient) -> None:
    url = '/organizations'
    john = test_dataset['users']['john']

    # unauthenticated user access
    resp = await client.post(url)
    assert resp.status_code == 401

    # john creates an organization
    org = OrganizationInsert(
        name='Mutantes', base_repo_role='reader', billing_address='Rua dos Bobos, 0'
    )
    await logged_session(client, john)
    resp = await client.post(url, json=org.dict())


async def test_show_organization(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    beatles = test_dataset['organizations']['beatles']
    monsters = test_dataset['organizations']['monsters']

    # unauthenticated user access
    resp = await client.get(f'/organizations/{beatles}')
    assert resp.status_code == 401

    # john's organizations
    await logged_session(client, john)
    resp = await client.get(f'/organizations/{beatles}')
    assert resp.status_code == 200
    org = resp.json()
    assert org['id'] == beatles

    # john is not a member of monsters
    resp = await client.get(f'/organizations/{monsters}')
    assert resp.status_code == 403

    # inexistent organization
    resp = await client.get('/organizations/0')
    assert resp.status_code == 404
