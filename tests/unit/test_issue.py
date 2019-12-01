from ghia import ghia_issue
import json
import pytest
import os


def fixtures_path():
    return os.path.dirname(os.path.realpath(__file__)) + '/fixtures/'

@pytest.fixture
def issue1_fixture():
    with open(fixtures_path() + 'issue1.json') as f:
        s = f.read()
    return json.loads(s)


def test_issue_class(issue1_fixture):
    issue = ghia_issue.Issue(issue1_fixture)
    assert issue.number == issue1_fixture["number"]
    assert issue.title == issue1_fixture["title"]
    assert issue.body == issue1_fixture["body"]
    assert issue.url == issue1_fixture["html_url"]
    assert issue.repo_slug == "octocat/Hello-World"
    assert issue.labels == set(['bug'])
    assert issue.assignees == set(['octocat'])

    update_json = issue.get_update_json()
    j = json.loads(update_json)
    assert j["labels"] == ['bug']
    assert j["assignees"] == ['octocat']
