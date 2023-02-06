from collections.abc import Iterable
from itertools import cycle

from faker import Faker

from .models import (
    issue,
    organization,
    repository,
    user,
    user_organization,
    user_repository,
)
from .models.issue import IssueInsert
from .models.organization import OrganizationInsert
from .models.repository import RepositoryInsert2
from .models.user import UserInsert
from .models.user_organization import UserOrganizationInfo
from .models.user_repository import UserRepositoryInfo


async def new_user(
    name: str | None = None, email: str | None = None, password: str | None = None
) -> int:
    fake = Faker()
    return await user.insert(
        UserInsert(
            name=name or fake.name(),
            email=email or fake.email(),
            password=password or fake.password(20),
        )
    )


async def new_organization(
    members: Iterable[int],
    name: str | None = None,
    billing_address: str | None = None,
    base_repo_role: str = 'reader',
    roles: Iterable[str] | None = None,
) -> int:
    """
    Create a new organization.
    """
    roles = roles or ('owner', 'member')
    fake = Faker()
    org_id = await organization.insert(
        OrganizationInsert(
            name=name or fake.company(),
            billing_address=billing_address or fake.address(),
            base_repo_role=base_repo_role,
        )
    )
    for member, role in zip(members, cycle(roles), strict=False):
        await user_organization.insert(
            UserOrganizationInfo(user_id=member, organization_id=org_id, role=role)
        )
    return org_id


async def new_repository(
    organization_id: int,
    members: Iterable[int],
    name: str | None = None,
    roles: Iterable[str] | None = None,
) -> int:
    roles = roles or ('admin', 'maintainer', 'reader')
    fake = Faker()
    repo_id = await repository.insert(
        RepositoryInsert2(
            name=name or fake.color_name(),
            organization_id=organization_id,
        )
    )
    for member, role in zip(members, cycle(roles), strict=False):
        await user_repository.insert(
            UserRepositoryInfo(repository_id=repo_id, user_id=member, role=role)
        )
    return repo_id


async def new_issue(repository_id: int, creator_id: int, title: str | None = None) -> int:
    fake = Faker()
    return await issue.insert(
        IssueInsert(
            title=title or fake.sentence(),
            repository_id=repository_id,
            creator_id=creator_id,
        )
    )


async def insert(name: str) -> int:
    email = f'{name}+test@email.com'
    return await new_user(name=name, email=email, password=email)


async def load_test_dataset() -> dict[str, dict[str, int]]:
    users = {
        'john': (john := await insert('john')),
        'paul': (paul := await insert('paul')),
        'mike': (mike := await insert('mike')),
        'sully': (sully := await insert('sully')),
        'ringo': (ringo := await insert('ringo')),
        'randall': (randall := await insert('randall')),
        'admin': await insert('admin'),
        'fulano': await insert('fulano'),
    }

    organizations = {
        'beatles': (
            beatles := await new_organization(
                name='The Beatles',
                members=(john, paul, ringo),
                roles=('owner', 'member', 'member'),
            )
        ),
        'monsters': (
            monsters := await new_organization(
                name='Monsters Inc.',
                members=(mike, sully, randall),
                roles=('owner', 'member', 'member'),
            )
        ),
    }

    repositories = {
        'abbey_road': await new_repository(
            name='Abbey Road',
            organization_id=beatles,
            members=(john, paul, mike),
            roles=['reader', 'admin', 'maintainer'],
        ),
        'the_white_album': await new_repository(
            name='The White Album',
            organization_id=beatles,
            members=(john, paul, ringo),
        ),  # not present in the original gitclub example
        'paperwork': await new_repository(
            name='Paperwork',
            organization_id=monsters,
            members=(sully, randall),
            roles=['reader', 'reader'],
        ),
    }

    issues = {
        'acclaim': await new_issue(
            repository_id=repositories['abbey_road'],
            creator_id=ringo,  # differs from the original gitclub example
        ),
        'traffic': await new_issue(
            repository_id=repositories['paperwork'],
            creator_id=sully,  # differs from the original gitclub example
        ),
    }

    # https://github.com/osohq/oso/blob/70965f2277d7167c38d3641140e6e97dec78e3bf/languages/python/sqlalchemy-oso/tests/test_roles.py#L132-L133

    return {
        'users': users,
        'organizations': organizations,
        'repositories': repositories,
        'issues': issues,
    }
