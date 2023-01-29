from typing import Type

from pydantic import BaseModel
from sqlalchemy import Table

from .models.organization import Organization, user_role_organization
from .models.repository import Repository, user_role_repository

from .schemas.user import UserInfo
from .schemas.repository import RepositoryInfo
from .schemas.organization import OrganizationInfo
from .schemas.issue import IssueInfo


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
repo_actions['admin'] = (
    repo_actions['reader']
    | repo_actions['maintainer']
    | {
        'create_role_assignments',
        'list_role_assignments',
        'update_role_assignments',
        'delete_role_assignments',
    }
)

# map organization roles to repository roles
# those roles shouldn't exist in the user_repository table
repo_actions['member'] = repo_actions['reader']
repo_actions['owner'] = repo_actions['admin']


# Issue Roles and actions

issue_actions = {}
# reader and maintainer depends on user's role in the repository
issue_actions['reader'] = {'read'}
issue_actions['maintainer'] = issue_actions['reader'] | {'update', 'close'}
issue_actions['creator'] = issue_actions['maintainer'] | {'reopen'}


ResourceType = BaseModel | Type[BaseModel | Table]


async def authorized(actor: BaseModel, action: str, resource: ResourceType) -> bool:
    match actor, resource:

        case UserInfo(id=actor_id), UserInfo(id=resource_id):
            role = actor_id == resource_id and 'owner' or 'reader'
            return action in user_actions[role]

        case UserInfo(id=user_id), Organization:
            return action == 'create'

        case UserInfo(id=user_id), OrganizationInfo(id=organization_id):
            role = await user_role_organization(user_id, organization_id)
            return bool(role) and action in org_actions[role]

        case UserInfo(id=user_id), RepositoryInfo(
            id=repository_id, organization_id=organization_id
        ):
            role = await user_role_repository(
                user_id, repository_id
            ) or await user_role_organization(user_id, organization_id)
            return bool(role) and action in repo_actions[role]

        case UserInfo(id=user_id), IssueInfo(repository_id=repository_id, creator_id=creator_id):
            role = (
                user_id == creator_id
                and 'creator'
                or await user_role_repository(user_id, repository_id)
            )
            return bool(role) and action in issue_actions[role]

    raise NotImplementedError(f'authorization not implemented for {actor} {action} {resource}')
