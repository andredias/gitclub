from fastapi import APIRouter, Response

from ..authorization import check_authz
from ..dependantions import CurrentUser, TargetIssue, TargetRepository
from ..models.issue import (
    IssueInfo,
    IssueInsert,
    IssuePatch,
    get,
    get_repository_issues,
    insert,
    update,
)
from ..resources import db

router = APIRouter(
    prefix='/organizations/{organization_id}/repositories/{repository_id}/issues', tags=['issues']
)


@router.get('')
async def list_issues(
    repos: TargetRepository,
    current_user: CurrentUser,
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
    repos: TargetRepository,
    current_user: CurrentUser,
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
    issue: TargetIssue,
    current_user: CurrentUser,
) -> IssueInfo:
    """
    Show an issue
    """
    await check_authz(current_user, 'read', issue)
    return issue


@router.put('/{issue_id}')
@router.patch('/{issue_id}')
async def close(
    issue: TargetIssue,
    current_user: CurrentUser,
) -> None:
    """
    Close an issue
    """
    await check_authz(current_user, 'close', issue)
    patch = IssuePatch(closed=True)
    await update(issue.id, patch)
    return await get(issue.id)  # type: ignore
