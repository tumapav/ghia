from ghia import create_app
import pytest
from tests.unit.helpers import betamax_setup, get_config_object


TOKEN, REPO, USER = betamax_setup()


@pytest.fixture
def test_client(betamax_session):
    app = create_app({
        "test": True,
        "session": betamax_session,
        "config": get_config_object('rules.sample3.cfg'),
        "TOKEN": TOKEN,
        "REPO": REPO,
        "SECRET": None
    })
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def test_client_with_secret(betamax_session):
    app = create_app({
        "test": True,
        "session": betamax_session,
        "config": get_config_object('rules.sample3.cfg'),
        "TOKEN": TOKEN,
        "REPO": REPO,
        "SECRET": "test_secret"
    })
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def opened_issue():
    return {
        "action": "labeled",
        "issue": {
            "number": 7,
            "title": "Test",
            "state": "open",
            "assignees": [],
            "body": "Test issue",
            "labels": [],
            "repository_url": "https://api.github.com/repos/"+REPO,
            "html_url": "https://github.com/"+REPO+"/issues/7",
        },
        "repository": {
            "full_name": REPO,
        }
    }


@pytest.fixture
def closed_issue():
    return {
        "action": "labeled",
        "issue": {
            "number": 7,
            "title": "Test",
            "state": "closed",
            "assignees": [],
            "body": "Test issue",
            "labels": [],
            "repository_url": "https://api.github.com/repos/" + REPO,
            "html_url": "https://github.com/" + REPO + "/issues/7",
        },
        "repository": {
            "full_name": REPO,
        }
    }


def test_web_ghia_main_page(test_client):
    html = test_client.get('/').get_data(as_text=True)

    # Name of the current user (from API)
    assert USER in html

    # Names of users from pattern file
    assert "octocat" in html
    assert "tester" in html

    # Patterns from pattern file
    assert "http[s]{0,1}://localhost:[0-9]{2,5}" in html
    assert "text" in html

    # Fallback label
    assert "Need assignment" in html


def test_webhook_ping_ok(test_client):
    res = test_client.post('/', json={}, headers={'X-GitHub-Event': 'ping'})
    text = res.get_data(as_text=True)
    assert text == "Ping OK"
    assert res.status_code == 200


def test_webhook_ping_signature_error_no_confsecret(test_client):
    with pytest.raises(ValueError) as e:
        test_client.post('/', json={}, headers={'X-GitHub-Event': 'ping',
                                                'X-Hub-Signature': 'sha1=wrong'})
    assert str(e.value) == "Signature verification failed."


def test_webhook_ping_signature_error_with_confsecret(test_client_with_secret):
    res = test_client_with_secret.post('/', json={}, headers={'X-GitHub-Event': 'ping',
                                                              'X-Hub-Signature': 'sha1=wrong'})
    text = res.get_data(as_text=True)
    assert text == "The request signature is wrong."
    assert res.status_code == 400


def test_webhook_ping_signature_error_bad_signature_format(test_client_with_secret):
    with pytest.raises(ValueError) as e:
        test_client_with_secret.post('/', json={}, headers={'X-GitHub-Event': 'ping',
                                                            'X-Hub-Signature': 'test'})
    assert str(e.value) == "Signature header has incorrect format."


def test_webhook_ping_signature_error_unsupported_digest(test_client_with_secret):
    with pytest.raises(ValueError) as e:
        test_client_with_secret.post('/', json={}, headers={'X-GitHub-Event': 'ping',
                                                            'X-Hub-Signature': 'sha512=test'})
    assert str(e.value) == "GitHub signatures are expected to use SHA1."


def test_webhook_ping_signature_correct(test_client_with_secret):
    res = test_client_with_secret.post('/', json={}, headers={'X-GitHub-Event': 'ping',
                                                              'X-Hub-Signature': 'sha1=17ab00a83f7f6e1c593ee44095aa1fd368af2b2e'})
    text = res.get_data(as_text=True)
    assert text == "Ping OK"
    assert res.status_code == 200


def test_webhook_ignored_action(test_client):
    res = test_client.post('/', json={}, headers={'X-GitHub-Event': 'ignored_event'})
    text = res.get_data(as_text=True)
    assert text == "Event type ignored."
    assert res.status_code == 200


def test_webhook_skip_closed_issues(test_client, closed_issue):
    res = test_client.post('/', json=closed_issue, headers={'X-GitHub-Event': 'issues'})
    text = res.get_data(as_text=True)
    assert text == "Closed issue is ignored."
    assert res.status_code == 200


def test_webhook_update_issue_ok(test_client, opened_issue):
    res = test_client.post('/', json=opened_issue, headers={'X-GitHub-Event': 'issues'})
    text = res.get_data(as_text=True)
    assert text == "Issue update done."
    assert res.status_code == 200
