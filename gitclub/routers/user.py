from fastapi import APIRouter

from ..authentication import CurrentUser
from ..authorization import authorized, check_authz
from ..dependantions import TargetUser
from ..models.repository import RepositoryInfo
from ..models.user import UserInfo
from ..models.user_repository import get_user_repositories

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/{id}')
async def get_user_info(
    user: TargetUser,
    current_user: CurrentUser,
) -> UserInfo:
    # authenticated_user can read any user's profile
    await check_authz(current_user, 'read_profile', user)
    return user


@router.get('/{id}/repos')
async def get_user_respositories(
    user: TargetUser,
    current_user: CurrentUser,
) -> list[RepositoryInfo]:
    # authenticated_user can read any user's profile
    await check_authz(current_user, 'read_profile', user)
    repos = await get_user_repositories(user.id)
    # but can only read repos that he has access to
    return [repo for repo in repos if await authorized(current_user, 'read', repo)]
