from .models import (
    issue,
    organization,
    repository,
    user,
    user_organization,
    user_repository,
)
from .schemas.issue import IssueInsert
from .schemas.organization import OrganizationInsert
from .schemas.repository import RepositoryInsert
from .schemas.user import UserInsert
from .schemas.user_organization import UserOrganizationInfo
from .schemas.user_repository import UserRepositoryInfo

emails = {
    'john': 'john@beatles.com',
    'paul': 'paul@beatles.com',
    'mike': 'mike@monsters.com',
    'ringo': 'ringo@beatles.com',
    'admin': 'admin@admin.com',
    'sully': 'sully@monsters.com',
    'randall': 'randall@monsters.com',
}


async def insert(name: str) -> int:
    return await user.insert(
        UserInsert(
            name=name,
            email=emails[name],
            password=emails[name],
        )
    )


async def load_fixture_data() -> None:

    # Users #

    john = await insert('john')
    paul = await insert('paul')
    mike = await insert('mike')
    sully = await insert('sully')
    ringo = await insert('ringo')
    randall = await insert('randall')
    await insert('admin')

    # Orgs #

    beatles = await organization.insert(
        OrganizationInsert(
            name='The Beatles',
            billing_address='64 Penny Ln Liverpool, UK',
            base_repo_role='reader',
        )
    )
    monsters = await organization.insert(
        OrganizationInsert(
            name='Monsters Inc.',
            billing_address='123 Scarers Rd Monstropolis, USA',
            base_repo_role='reader',
        )
    )

    # Repos #

    abby_road = await repository.insert(
        RepositoryInsert(name='Abbey Road', organization_id=beatles)
    )
    paperwork = await repository.insert(
        RepositoryInsert(name='Paperwork', organization_id=monsters)
    )

    # Issues #

    await issue.insert(IssueInsert(title='Too much critical acclaim', repo=abby_road))

    # https://github.com/osohq/oso/blob/70965f2277d7167c38d3641140e6e97dec78e3bf/languages/python/sqlalchemy-oso/tests/test_roles.py#L132-L133

    # Repo roles #

    await user_repository.insert(
        UserRepositoryInfo(user_id=john, repository_id=abby_road, role='reader')
    )
    await user_repository.insert(
        UserRepositoryInfo(user_id=paul, repository_id=abby_road, role='reader')
    )
    await user_repository.insert(
        UserRepositoryInfo(name=ringo, repository_id=abby_road, role='maintainer')
    )
    await user_repository.insert(
        UserRepositoryInfo(name=mike, repository_id=paperwork, role='reader')
    )
    await user_repository.insert(
        UserRepositoryInfo(name=sully, repository_id=paperwork, role='reader')
    )

    # Org roles #

    await user_organization.insert(
        UserOrganizationInfo(user_id=john, organization_id=beatles, role='owner')
    )
    await user_organization.insert(
        UserOrganizationInfo(name=paul, organization_id=beatles, role='member')
    )
    await user_organization.insert(
        UserOrganizationInfo(name=ringo, organization_id=beatles, role='member')
    )
    await user_organization.insert(
        UserOrganizationInfo(name=mike, organization_id=monsters, role='owner')
    )
    await user_organization.insert(
        UserOrganizationInfo(name=sully, organization_id=monsters, role='member')
    )
    await user_organization.insert(
        UserOrganizationInfo(name=randall, organization_id=monsters, role='member')
    )
