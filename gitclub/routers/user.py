from fastapi import APIRouter, Depends, HTTPException

from ..authentication import authenticated_user
from ..authorization import authorized, check_authz
from ..models.user import get_user
from ..models.user_repository import user_repositories
from ..schemas.repository import RepositoryInfo
from ..schemas.user import UserInfo

router = APIRouter(prefix='/users', tags=['users'])


async def target_user(id_: int) -> UserInfo:
    user = await get_user(id_)
    if not user:
        raise HTTPException(404)
    return user


@router.get('/{id_}')
async def get_user_info(
    user: UserInfo = Depends(target_user),
    current_user: UserInfo = Depends(authenticated_user),
) -> UserInfo:
    # authenticated_user can read any user's profile
    await check_authz(current_user, 'read_profile', user)
    return user


@router.get('/{id_}/repos')
async def get_user_respositories(
    user: UserInfo = Depends(target_user),
    current_user: UserInfo = Depends(authenticated_user),
) -> list[RepositoryInfo]:
    # authenticated_user can read any user's profile
    await check_authz(current_user, 'read_profile', user)
    repos = await user_repositories(user.id)
    # but can only read repos that he has access to
    return [repo for repo in repos if await authorized(current_user, 'read', repo)]
