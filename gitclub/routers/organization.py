from fastapi import APIRouter, Depends, HTTPException

from ..authentication import authenticated_user
from ..authorization import check_authz
from ..models import organization
from ..models.organization import Organization, OrganizationInfo, OrganizationInsert
from ..models.user import UserInfo
from ..models.user_organization import UserOrganizationInfo, user_organizations
from ..models.user_organization import insert as insert_user_organization

router = APIRouter(prefix='/organizations', tags=['organizations'])


async def get_organization(organization_id: int) -> OrganizationInfo:
    org = await organization.get(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail='Organization not found')
    return org


@router.get('')
async def list_organizations(
    current_user: UserInfo = Depends(authenticated_user),
) -> list[OrganizationInfo]:
    """
    List all organizations the user is a member of.
    """
    # it doesn't make sense to check authorization for each organization the user is a member of
    # because if he/she is a member, he/she has read access to it at least
    # result = [org for org in organizations if await authorized(current_user, 'read', org)]  # noqa: ERA001, E501
    return await user_organizations(current_user.id)


@router.post('', status_code=201)
async def create(
    new_org: OrganizationInsert,
    current_user: UserInfo = Depends(authenticated_user),
) -> None:
    await check_authz(current_user, 'create', Organization)
    org_id = await organization.insert(new_org)
    user_org = UserOrganizationInfo(organization_id=org_id, user_id=current_user.id, role='owner')
    await insert_user_organization(user_org)
    return


@router.get('/{organization_id}')
async def show(
    org: OrganizationInfo = Depends(get_organization),
    current_user: UserInfo = Depends(authenticated_user),
) -> OrganizationInfo:
    await check_authz(current_user, 'read', org)
    return org
