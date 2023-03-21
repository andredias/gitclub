from typing import Annotated

from fastapi import Depends, HTTPException, status

from .authentication import CurrentUser
from .authorization import check_authz
from .models import issue, organization, repository, user
from .models.issue import IssueInfo
from .models.organization import OrganizationInfo
from .models.repository import RepositoryInfo
from .models.user import UserInfo


async def target_user(id: int) -> UserInfo:
    user_ = await user.get(id)
    if not user_:
        raise HTTPException(404)
    return user_


TargetUser = Annotated[UserInfo, Depends(target_user)]


async def get_organization(organization_id: int) -> OrganizationInfo:
    org = await organization.get(organization_id)
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Organization not found')
    return org


TargetOrganization = Annotated[OrganizationInfo, Depends(get_organization)]


async def get_repository(
    repository_id: int,
    org: TargetOrganization,
    current_user: CurrentUser,
) -> RepositoryInfo:
    repo = await repository.get(repository_id, organization_id=org.id)
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='Repository not found')
    await check_authz(current_user, 'read', repo)
    return repo


TargetRepository = Annotated[RepositoryInfo, Depends(get_repository)]


async def get_issue(
    organization_id: int,
    repository_id: int,
    issue_id: int,
) -> IssueInfo:
    issue_ = await issue.get(issue_id, repository_id=repository_id, organization_id=organization_id)
    if not issue_:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue_


TargetIssue = Annotated[IssueInfo, Depends(get_issue)]
