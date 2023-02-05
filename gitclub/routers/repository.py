from fastapi import APIRouter, Depends, HTTPException, Response

from ..authentication import authenticated_user
from ..authorization import authorized, check_authz
from ..models.repository import get, get_organization_repositories, insert
from ..resources import db
from ..schemas.organization import OrganizationInfo
from ..schemas.repository import RepositoryInfo, RepositoryInsert, RepositoryInsert2
from ..schemas.user import UserInfo
from .organization import get_organization

router = APIRouter(prefix='/organizations/{organization_id}/repositories', tags=['repositories'])


async def get_repository(
    repository_id: int,
    org: OrganizationInfo = Depends(get_organization),
    current_user: UserInfo = Depends(authenticated_user),
) -> RepositoryInfo:
    repository = await get(repository_id, organization_id=org.id)
    if not repository:
        raise HTTPException(status_code=404, detail='Repository not found')
    await check_authz(current_user, 'read', repository)
    return repository


@router.get('')
async def list_repositories(
    org: OrganizationInfo = Depends(get_organization),
    current_user: UserInfo = Depends(authenticated_user),
) -> list[RepositoryInfo]:
    """
    List all repositories of a group.
    """
    await check_authz(current_user, 'list_repos', org)
    repositories = await get_organization_repositories(org.id)
    return [repo for repo in repositories if await authorized(current_user, 'read', repo)]


@router.post('', status_code=201)
@db.transaction()
async def create_repository(
    new_repo: RepositoryInsert,
    response: Response,
    org: OrganizationInfo = Depends(get_organization),
    current_user: UserInfo = Depends(authenticated_user),
) -> RepositoryInfo:
    """
    Create a new repository.
    """
    await check_authz(current_user, 'create_repos', org)
    new_repo = RepositoryInsert2(**new_repo.dict(), organization_id=org.id)
    repo_id = await insert(new_repo)
    response.headers['Location'] = f'/organizations/{org.id}/repositories/{repo_id}'
    return RepositoryInfo(id=repo_id, **new_repo.dict())


@router.get('/{repository_id}')
async def show(
    repository: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> RepositoryInfo:
    """
    Show a repository
    """
    await check_authz(current_user, 'read', repository)
    return repository
