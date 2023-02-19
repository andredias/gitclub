from asyncpg import UniqueViolationError
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status

from ..authentication import authenticated_user
from ..authorization import authorized, check_authz, check_resource_role
from ..models.organization import OrganizationInfo
from ..models.repository import (
    RepositoryInfo,
    RepositoryInsert,
    RepositoryInsert2,
    get,
    get_organization_repositories,
    insert,
)
from ..models.user import UserInfo
from ..models.user import get as get_user
from ..models.user_repository import (
    RepositoryMemberInfo,
    UserRepositoryInfo,
    delete_user_repository,
    get_repository_members,
    get_repository_non_members,
    get_user_role_in_repository,
    update_user_repository,
)
from ..models.user_repository import insert as insert_user_repository
from ..resources import db
from .organization import get_organization

router = APIRouter(prefix='/organizations/{organization_id}/repositories', tags=['repositories'])


async def get_repository(
    repository_id: int,
    org: OrganizationInfo = Depends(get_organization),
    current_user: UserInfo = Depends(authenticated_user),
) -> RepositoryInfo:
    repository = await get(repository_id, organization_id=org.id)
    if not repository:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Repository not found')
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


@router.post('', status_code=status.HTTP_201_CREATED)
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


# the remaining endpoints were originally in
# https://github.com/osohq/gitclub/blob/main/backends/flask-sqlalchemy/app/routes/role_assignments.py


@router.get('/{repository_id}/non-members')
async def list_non_members(
    repository: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> list[UserInfo]:
    """
    List all users who aren't members of the repository.
    """
    await check_authz(current_user, 'list_role_assignments', repository)
    users = await get_repository_non_members(repository.id)
    return [user for user in users if await authorized(current_user, 'read_profile', user)]


@router.get('/{repository_id}/members')
async def list_members(
    repository: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> list[RepositoryMemberInfo]:
    """
    List all members of the repository.
    """
    await check_authz(current_user, 'list_role_assignments', repository)
    users = await get_repository_members(repository.id)
    return [user for user in users if await authorized(current_user, 'read_profile', user)]


@router.post('/{repository_id}/members', status_code=status.HTTP_201_CREATED)
@db.transaction()
async def add_member(
    response: Response,
    user_id: int = Body(...),
    role: str = Body(...),
    repository: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> UserRepositoryInfo:
    """
    Add a member to a repository.
    """
    await check_authz(current_user, 'create_role_assignments', repository)
    target_user = await get_user(user_id)
    if not target_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='User not found')
    await check_authz(current_user, 'read_profile', target_user)
    check_resource_role('repository', role)
    record = UserRepositoryInfo(user_id=user_id, repository_id=repository.id, role=role)
    try:
        await insert_user_repository(record)
    except UniqueViolationError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail='User is already a member') from None
    response.headers['Location'] = (
        f'/organizations/{repository.organization_id}'
        f'/repositories/{repository.id}/members/{user_id}'
    )
    return record


@router.put('/{repository_id}/members/{user_id}')
@db.transaction()
async def update_member_role(
    user_id: int,
    role: str = Body(embed=True),
    repository: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> UserRepositoryInfo:
    """
    Update the role of a user in the repository.
    """
    await check_authz(current_user, 'update_role_assignments', repository)
    current_role = await get_user_role_in_repository(user_id=user_id, repository_id=repository.id)
    if not current_role:
        raise HTTPException(status_code=404, detail='Member not found')
    if role != current_role:
        check_resource_role('repository', role)
        await update_user_repository(user_id=user_id, repository_id=repository.id, role=role)
    return UserRepositoryInfo(user_id=user_id, repository_id=repository.id, role=role)


@router.delete('/{repository_id}/members/{user_id}', status_code=204)
@db.transaction()
async def remove_member(
    user_id: int,
    repository: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> None:
    """
    Delete the role of a user in the organization.
    """
    if current_user.id != user_id:
        await check_authz(current_user, 'delete_role_assignments', repository)
    await delete_user_repository(user_id, repository.id)
    return
