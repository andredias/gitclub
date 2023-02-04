from gitclub.authorization import authorized, issue_actions, org_actions, repo_actions, user_actions
from gitclub.models import issue, organization, repository, user

TestData = dict[str, dict[str, int]]


async def test_authorization(test_dataset: TestData) -> None:
    john = await user.get(test_dataset['users']['john'])
    paul = await user.get(test_dataset['users']['paul'])
    sully = await user.get(test_dataset['users']['sully'])

    assert john and paul and sully

    for action in user_actions['reader']:
        assert await authorized(john, action, john)
        assert await authorized(john, action, paul)

    for action in user_actions['owner'] - user_actions['reader']:
        assert await authorized(john, action, john)
        assert not await authorized(john, action, paul)

    # organization

    # john is an owner of the beatles
    # paul is a member of the beatles
    # sully is not a member of the beatles

    beatles = await organization.get(test_dataset['organizations']['beatles'])

    assert beatles
    assert await authorized(john, 'create', organization.Organization)

    for action in org_actions['member']:
        assert await authorized(john, action, beatles)
        assert await authorized(paul, action, beatles)
        assert not await authorized(sully, action, beatles)

    for action in org_actions['owner'] - org_actions['member']:
        assert await authorized(john, action, beatles)
        assert not await authorized(paul, action, beatles)
        assert not await authorized(sully, action, beatles)

    # repository

    # john is a reader of abbey_road
    # paul is an admin of abbey_road
    # ringo is an indirect reader of abbey_road
    # mike is a maintainer of abbey_road
    # sully is not related to abbey_road

    abbey_road = await repository.get(test_dataset['repositories']['abbey_road'])

    ringo = await user.get(test_dataset['users']['ringo'])
    mike = await user.get(test_dataset['users']['mike'])

    assert abbey_road and ringo and mike

    for action in repo_actions['reader']:
        assert await authorized(john, action, abbey_road)
        assert await authorized(paul, action, abbey_road)
        assert await authorized(ringo, action, abbey_road)
        assert await authorized(mike, action, abbey_road)
        assert not await authorized(sully, action, abbey_road)

    for action in repo_actions['maintainer'] - repo_actions['reader']:
        assert not await authorized(john, action, abbey_road)
        assert await authorized(paul, action, abbey_road)
        assert not await authorized(ringo, action, abbey_road)
        assert await authorized(mike, action, abbey_road)
        assert not await authorized(sully, action, abbey_road)

    for action in repo_actions['admin'] - repo_actions['maintainer']:
        assert not await authorized(john, action, abbey_road)
        assert await authorized(paul, action, abbey_road)
        assert not await authorized(ringo, action, abbey_road)
        assert not await authorized(mike, action, abbey_road)
        assert not await authorized(sully, action, abbey_road)

    # Issue

    # ringo is the author of the issue

    ticket = await issue.get(test_dataset['issues']['acclaim'])

    assert ticket

    for action in issue_actions['reader']:
        assert await authorized(john, action, ticket)
        assert await authorized(paul, action, ticket)
        assert await authorized(ringo, action, ticket)
        assert await authorized(mike, action, ticket)
        assert not await authorized(sully, action, ticket)

    for action in issue_actions['maintainer'] - issue_actions['reader']:
        assert not await authorized(john, action, ticket)
        assert await authorized(paul, action, ticket)
        assert await authorized(ringo, action, ticket)
        assert await authorized(mike, action, ticket)
        assert not await authorized(sully, action, ticket)

    for action in issue_actions['creator'] - issue_actions['maintainer']:
        assert not await authorized(john, action, ticket)
        assert await authorized(paul, action, ticket)
        assert await authorized(ringo, action, ticket)
        assert not await authorized(mike, action, ticket)
        assert not await authorized(sully, action, ticket)
