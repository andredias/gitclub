from fastapi import status
from httpx import AsyncClient

from gitclub.models.organization import OrganizationInsert

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
    assert resp.status_code == 201
    data = resp.json()
    assert org
    assert resp.headers['Location'] == f'/organizations/{data["id"]}'


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


async def test_add_member(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    url = f'/organizations/{beatles}/members'

    # unauthenticated user access
    resp = await client.post(url)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # paul is not authorized to add members
    await logged_session(client, paul)
    resp = await client.post(url, json={'user_id': fulano, 'role': 'member'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # paul is already a member
    await logged_session(client, john)
    resp = await client.post(url, json={'user_id': paul, 'role': 'member'})
    assert resp.status_code == status.HTTP_409_CONFLICT

    # invalid role
    resp = await client.post(url, json={'user_id': fulano, 'role': 'maintainer'})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # john adds fulano as a member
    resp = await client.post(url, json={'user_id': fulano, 'role': 'member'})
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data['user_id'] == fulano
    assert data['role'] == 'member'
    assert data['organization_id'] == beatles
    assert resp.headers['Location'] == f'/organizations/{beatles}/members/{fulano}'


async def test_update_member_role(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']

    # unauthenticated user access
    url = f'/organizations/{beatles}/members/{fulano}'
    resp = await client.put(url, json={'role': 'owner'})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # paul is not authorized to update members
    url = f'/organizations/{beatles}/members/{john}'
    await logged_session(client, paul)
    resp = await client.put(url, json={'role': 'owner'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # paul is not authorized to update his own role
    url = f'/organizations/{beatles}/members/{paul}'
    resp = await client.put(url, json={'role': 'owner'})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # fulano is not a member of beatles
    url = f'/organizations/{beatles}/members/{fulano}'
    await logged_session(client, john)
    resp = await client.put(url, json={'role': 'owner'})
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    # john updates invalid role
    url = f'/organizations/{beatles}/members/{paul}'
    resp = await client.put(url, json={'role': 'maintainer'})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # john updates paul's role
    resp = await client.put(url, json={'role': 'owner'})
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data['user_id'] == paul
    assert data['role'] == 'owner'
    assert data['organization_id'] == beatles


async def test_remove_member(test_dataset: TestData, client: AsyncClient) -> None:
    john = test_dataset['users']['john']
    paul = test_dataset['users']['paul']
    ringo = test_dataset['users']['ringo']
    fulano = test_dataset['users']['fulano']
    beatles = test_dataset['organizations']['beatles']
    url = f'/organizations/{beatles}/members/{{}}'

    # unauthenticated user access
    resp = await client.delete(url.format(fulano))
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # paul is not authorized to remove members
    await logged_session(client, paul)
    resp = await client.delete(url.format(john))
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # paul should be able to remove himself
    resp = await client.delete(url.format(paul))
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # john tries to remove fulano, but he is not a member
    await logged_session(client, john)
    resp = await client.delete(url.format(fulano))
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # john removes ringo
    resp = await client.delete(url.format(ringo))
    assert resp.status_code == status.HTTP_204_NO_CONTENT
