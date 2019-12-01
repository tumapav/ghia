from ghia import ghia_issue
from ghia import ghia_requests
import json
import pytest
from tests.unit.helpers import betamax_setup, fixtures_path


@pytest.fixture
def issue1_fixture():
    with open(fixtures_path() + 'issue1.json') as f:
        s = f.read()
    return json.loads(s)


TOKEN, REPO, USER = betamax_setup()


def get_ghia_requests(betamax_session):
    betamax_session.headers.update({'Accept-Encoding': 'identity'})
    return ghia_requests.GhiaRequests(TOKEN, REPO, session=betamax_session)


def get_ghia_requests_wrong(betamax_session):
    betamax_session.headers.update({'Accept-Encoding': 'identity'})
    return ghia_requests.GhiaRequests("wrong_token", REPO, session=betamax_session)


def test_get_user(betamax_session):
    g = get_ghia_requests(betamax_session)
    user = g.get_user()
    assert user is not None
    assert "login" in user
    assert len(user["login"]) > 0


def test_get_user_fail(betamax_session):
    g = get_ghia_requests_wrong(betamax_session)
    with pytest.raises(RuntimeError) as e:
        g.get_user()
    assert str(e.value) == "Could not fetch Github user identity."


def test_get_issues(betamax_session):
    g = get_ghia_requests(betamax_session)
    issues = g.get_issues()
    assert issues is not None
    assert len(issues) == 112
    issue = issues[0]
    assert issue.number > 0
    assert issue.title == "Dummy"
    assert issue.body == "Just dummy a issue :duck:"
    assert issue.url == f"https://github.com/{REPO}/issues/{issue.number}"
    assert issue.repo_slug == REPO
    assert issue.labels == set(['Need assignment'])
    assert issue.assignees == set()


def test_get_issues_fail(betamax_session):
    g = get_ghia_requests_wrong(betamax_session)
    with pytest.raises(SystemExit) as e:
        issues = g.get_issues()
    assert e.type == SystemExit
    assert e.value.code == 10


def test_get_issues_update_issue_fail(betamax_session, issue1_fixture):
    g = get_ghia_requests_wrong(betamax_session)
    issue = ghia_issue.Issue(issue1_fixture)
    result = g.update_issue(issue)
    assert result is None


def test_get_issues_update_issue_fail_bad_assignee(betamax_session, issue1_fixture):
    g = get_ghia_requests(betamax_session)
    issues = g.get_issues()
    issue = issues[0]
    issue.assignees.add('.')
    result = g.update_issue(issue)
    issue.assignees.remove('.')
    assert result is None


def test_get_issues_update_issue(betamax_session):
    g = get_ghia_requests(betamax_session)

    issues = g.get_issues()
    issue = issues[0]
    orig_labels_count = len(issue.labels)
    orig_assignees_count = len(issue.assignees)
    assert issue.assignees == set()
    issue.assignees.add('ghia-jane')
    issue.labels.add('added_label')
    print("Update1: "+str(issue))
    updated_issue = g.update_issue(issue)
    assert updated_issue is not None
    assert 'ghia-jane' in updated_issue.assignees
    assert 'added_label' in updated_issue.labels

    updated_issue.assignees.remove('ghia-jane')
    updated_issue.labels.remove('added_label')
    print("Update2: " + str(updated_issue))
    updated_issue = g.update_issue(updated_issue)
    assert updated_issue is not None
    assert 'ghia-jane' not in updated_issue.assignees
    assert 'added_label' not in updated_issue.labels

    assert orig_labels_count == len(updated_issue.labels)
    assert orig_assignees_count == len(updated_issue.assignees)
