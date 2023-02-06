from typing import Type

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import Table

from .models.issue import IssueInfo
from .models.organization import Organization, OrganizationInfo
from .models.repository import RepositoryInfo
from .models.user import UserInfo
from .models.user_organization import get_user_role_in_organization
from .models.user_repository import get_user_role_in_repository


# User Roles and actions

user_actions = {}
user_actions['reader'] = {'read_profile'}
user_actions['owner'] = user_actions['reader'] | {'update_profile', 'delete_profile'}

# Organization Roles and actions

org_actions = {}
org_actions['member'] = {
    'read',
    'list_repos',
    'list_role_assignments',
}
org_actions['owner'] = org_actions['member'] | {
    'create_repos',
    'create_role_assignments',
    'update_role_assignments',
    'delete_role_assignments',
}


# Repository Roles and actions

repo_actions = {}
repo_actions['reader'] = {'read', 'list_issues', 'create_issues'}
repo_actions['maintainer'] = repo_actions['reader']
repo_actions['admin'] = repo_actions['maintainer'] | {
    'create_role_assignments',
    'list_role_assignments',
    'update_role_assignments',
    'delete_role_assignments',
}

# map organization roles to repository roles
# those roles shouldn't exist in the user_repository table
repo_actions['member'] = repo_actions['reader']
repo_actions['owner'] = repo_actions['admin']


# Issue Roles and actions

issue_actions = {}
# reader and maintainer depends on user's role in the repository
# not exactly equal to the original gitclug example
issue_actions['reader'] = {'read'}
issue_actions['maintainer'] = issue_actions['reader'] | {'update', 'close'}
issue_actions['creator'] = issue_actions['maintainer'] | {'reopen'}

# map repository roles to issue roles
issue_actions['admin'] = issue_actions['creator']

# map organization roles to issue roles
issue_actions['member'] = issue_actions['reader']
issue_actions['owner'] = issue_actions['creator']

ResourceType = BaseModel | Type[BaseModel | Table]


async def authorized(actor: BaseModel, action: str, resource: ResourceType) -> bool:
    role: str | None = None
    match resource, actor:  # noqa: E999

        case UserInfo(id=resource_id), UserInfo(id=actor_id):
            role = actor_id == resource_id and 'owner' or 'reader'
            return action in user_actions[role]

        case OrganizationInfo(id=organization_id), UserInfo(id=user_id):
            role = await get_user_role_in_organization(user_id, organization_id)
            return bool(role and action in org_actions[role])

        # case Organization, UserInfo(id=user_id) doesn't work
        # case Organization() also doesn't work since 'Table' object is not callable
        # see: https://stackoverflow.com/a/70817669
        case Org, UserInfo(id=user_id) if Org is Organization:
            return action == 'create'

        case RepositoryInfo(id=repository_id, organization_id=organization_id), UserInfo(
            id=user_id
        ):
            role = await get_user_role_in_repository(
                user_id, repository_id
            ) or await get_user_role_in_organization(user_id, organization_id)
            return bool(role and action in repo_actions[role])

        case IssueInfo(repository_id=repository_id, creator_id=creator_id), UserInfo(id=user_id):
            role = (
                user_id == creator_id
                and 'creator'
                or await get_user_role_in_repository(user_id, repository_id)
            )
            return bool(role and action in issue_actions[role])

    raise NotImplementedError(f'authorization not implemented for {actor} {action} {resource}')


async def check_authz(actor: BaseModel, action: str, resource: ResourceType) -> bool:
    if not await authorized(actor, action, resource):
        raise HTTPException(403)
    return True
