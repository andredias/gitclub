from fastapi import APIRouter

from ..authentication import CurrentUser
from ..authorization import action_to_roles, authorized, check_authz
from ..dependantions import TargetUser
from ..models.repository import RepositoryInfo, get_allowed_repositories
from ..models.user import UserInfo

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/{id}')
async def get_user_info(
    user: TargetUser,
    current_user: CurrentUser,
) -> UserInfo:
    # authenticated_user can read any user's profile
    await check_authz(current_user, 'read_profile', user)
    return user


@router.get('/{id}/repositories')
async def get_user_respositories(
    user: TargetUser,
    current_user: CurrentUser,
) -> list[RepositoryInfo]:
    """
    Return all repositories that a user has access to via membership to an organization
    or direct access to a repository.
    Only return repositories that current_user has also access to.
    """
    # authenticated_user can read any user's profile
    await check_authz(current_user, 'read_profile', user)
    repo_roles = list(action_to_roles('read', 'repository'))
    org_roles = list(action_to_roles('list_repos', 'organization'))
    repos = await get_allowed_repositories(user.id, repo_roles=repo_roles, org_roles=org_roles)
    # but can only read repos that authenticated user (current_user) has access to
    if current_user.id == user.id:
        return repos
    return [repo for repo in repos if await authorized(current_user, 'read', repo)]
