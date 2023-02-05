from fastapi import APIRouter, Depends, HTTPException, Response

from ..authentication import authenticated_user
from ..authorization import check_authz
from ..models.issue import get, get_repository_issues, insert, update
from ..resources import db
from ..schemas.issue import IssueInfo, IssueInsert, IssuePatch
from ..schemas.repository import RepositoryInfo
from ..schemas.user import UserInfo
from .repository import get_repository

router = APIRouter(
    prefix='/organizations/{organization_id}/repositories/{repository_id}/issues', tags=['issues']
)


async def get_issue(
    organization_id: int,
    repository_id: int,
    issue_id: int,
) -> IssueInfo:
    issue = await get(issue_id, repository_id=repository_id, organization_id=organization_id)
    if not issue:
        raise HTTPException(status_code=404, detail='Issue not found')
    return issue


@router.get('')
async def list_issues(
    repos: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> list[IssueInfo]:
    """
    List all issues of a repository.
    """
    await check_authz(current_user, 'list_issues', repos)
    issues = await get_repository_issues(repos.id)
    return list(issues)  # no extra authz check needed


@router.post('', status_code=201)
@db.transaction()
async def create_issue(
    data: IssueInsert,
    response: Response,
    repos: RepositoryInfo = Depends(get_repository),
    current_user: UserInfo = Depends(authenticated_user),
) -> IssueInfo:
    """
    Create a new issue.
    """
    await check_authz(current_user, 'create_issues', repos)
    issue_id = await insert(data)
    response.headers['Location'] = (
        f'{router.prefix.format(organization_id=repos.organization_id, repository_id=repos.id)}'
        f'/{issue_id}'
    )
    return await get(issue_id)  # type: ignore


@router.get('/{issue_id}')
async def show(
    issue: IssueInfo = Depends(get_issue),
    current_user: UserInfo = Depends(authenticated_user),
) -> IssueInfo:
    """
    Show an issue
    """
    await check_authz(current_user, 'read', issue)
    return issue


@router.put('/{issue_id}')
@router.patch('/{issue_id}')
async def close(
    issue: IssueInfo = Depends(get_issue),
    current_user: UserInfo = Depends(authenticated_user),
) -> None:
    """
    Close an issue
    """
    await check_authz(current_user, 'close', issue)
    patch = IssuePatch(closed=True)
    await update(issue.id, patch)
    return await get(issue.id)  # type: ignore
