from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Body, HTTPException, Response, status

from ..authentication import CurrentUser
from ..authorization import authorized, check_authz, check_resource_role
from ..dependantions import TargetOrganization
from ..models import organization, user
from ..models.organization import Organization, OrganizationInfo, OrganizationInsert
from ..models.user import UserInfo
from ..models.user_organization import (
    OrganizationMemberInfo,
    UserOrganizationInfo,
    delete_user_organization,
    get_organization_members,
    get_organization_non_members,
    get_user_organizations,
    get_user_role_in_organization,
    update_user_organization,
)
from ..models.user_organization import insert as insert_user_organization
from ..resources import db

router = APIRouter(prefix='/organizations', tags=['organizations'])


@router.get('')
async def list_organizations(
    current_user: CurrentUser,
) -> list[OrganizationInfo]:
    """
    List all organizations the user is a member of.
    """
    # it doesn't make sense to check authorization for each organization the user is a member of
    # because if he/she is a member, he/she has read access to it at least
    # result = [org for org in organizations if await authorized(current_user, 'read', org)]  # noqa: ERA001, E501
    return await get_user_organizations(current_user.id)


@router.post('', status_code=201)
@db.transaction()
async def create(
    new_org: OrganizationInsert,
    response: Response,
    current_user: CurrentUser,
) -> OrganizationInfo:
    await check_authz(current_user, 'create', Organization)
    org_id = await organization.insert(new_org)
    user_org = UserOrganizationInfo(organization_id=org_id, user_id=current_user.id, role='owner')
    await insert_user_organization(user_org)
    response.headers['Location'] = f'{router.prefix}/{org_id}'
    return OrganizationInfo(id=org_id, **new_org.dict())


@router.get('/{organization_id}')
async def show(
    org: TargetOrganization,
    current_user: CurrentUser,
) -> OrganizationInfo:
    await check_authz(current_user, 'read', org)
    return org


# the remaining endpoints were originally in
# gitclub/flask-alchemy/app/routes/role_assignment.py

# was: /unassigned_users
@router.get('/{organization_id}/non-members')
async def list_non_members(
    org: TargetOrganization,
    current_user: CurrentUser,
) -> list[UserInfo]:
    """
    List all users who aren't members of the organization.
    """
    await check_authz(current_user, 'list_role_assignments', org)
    users = await get_organization_non_members(org.id)
    return [user for user in users if await authorized(current_user, 'read_profile', user)]


# was: /role_assignments
@router.get('/{organization_id}/members')
async def list_members(
    org: TargetOrganization,
    current_user: CurrentUser,
) -> list[OrganizationMemberInfo]:
    """
    List all members of the organization.
    """
    await check_authz(current_user, 'list_role_assignments', org)
    members = await get_organization_members(org.id)
    return [
        user
        for user in members
        if await authorized(current_user, 'read_profile', UserInfo(**user.dict()))
    ]


# it was originally POST /role_assignments
@router.post('/{organization_id}/members', status_code=201)
@db.transaction()
async def add_member(
    response: Response,
    org: TargetOrganization,
    current_user: CurrentUser,
    user_id: int = Body(...),
    role: str = Body(...),
) -> UserOrganizationInfo:
    """
    Add a user to the organization.
    """
    await check_authz(current_user, 'create_role_assignments', org)
    target_user = await user.get(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail='User not found')
    await check_authz(current_user, 'read_profile', target_user)
    check_resource_role('organization', role)
    user_org = UserOrganizationInfo(organization_id=org.id, user_id=target_user.id, role=role)
    try:
        await insert_user_organization(user_org)
    except UniqueViolationError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail='Member already exists') from None
    response.headers['Location'] = f'{router.prefix}/{org.id}/members/{target_user.id}'
    return user_org


@router.put('/{organization_id}/members/{user_id}')
@db.transaction()
async def update_member_role(
    user_id: int,
    org: TargetOrganization,
    current_user: CurrentUser,
    role: str = Body(embed=True),
) -> UserOrganizationInfo:
    """
    Update the role of a user in the organization.
    """
    await check_authz(current_user, 'update_role_assignments', org)
    current_role = await get_user_role_in_organization(user_id=user_id, organization_id=org.id)
    if not current_role:
        raise HTTPException(status_code=404, detail='Member not found')
    if role != current_role:
        check_resource_role('organization', role)
        await update_user_organization(user_id, org.id, role)
    return UserOrganizationInfo(user_id=user_id, organization_id=org.id, role=role)


@router.delete('/{organization_id}/members/{user_id}', status_code=204)
@db.transaction()
async def remove_member(
    user_id: int,
    org: TargetOrganization,
    current_user: CurrentUser,
) -> None:
    """
    Delete the role of a user in the organization.
    """
    if current_user.id != user_id:
        await check_authz(current_user, 'delete_role_assignments', org)
    await delete_user_organization(user_id, org.id)
