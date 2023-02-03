from fastapi import APIRouter, Depends, HTTPException

from ..authentication import authenticated_user
from ..authorization import check_authz
from ..models.organization import Organization, get
from ..models.organization import insert as insert_organization
from ..models.user_organization import insert as insert_user_organization
from ..models.user_organization import user_organizations
from ..schemas.organization import OrganizationInfo, OrganizationInsert
from ..schemas.user import UserInfo
from ..schemas.user_organization import UserOrganizationInfo

router = APIRouter(prefix='/organizations', tags=['organizations'])


@router.get('')
async def index(current_user: UserInfo = Depends(authenticated_user)) -> list[OrganizationInfo]:
    organizations = await user_organizations(current_user.id)
    # it doesn't make sense to check authorization for each organization the user is a member of
    # result = [org for org in organizations if await authorized(current_user, 'read', org)]  # noqa: ERA001, E501
    return organizations  # noqa: RET504


@router.post('', status_code=201)
async def create(
    new_org: OrganizationInsert,
    current_user: UserInfo = Depends(authenticated_user),
) -> None:
    await check_authz(current_user, 'create', Organization)
    org_id = await insert_organization(new_org)
    user_org = UserOrganizationInfo(organization_id=org_id, user_id=current_user.id, role='owner')
    await insert_user_organization(user_org)
    return


@router.get('/{id}')
async def show(id: int, current_user: UserInfo = Depends(authenticated_user)) -> OrganizationInfo:
    org = await get(id)
    if not org:
        raise HTTPException(status_code=404, detail='Organization not found')
    await check_authz(current_user, 'read', org)
    return org
