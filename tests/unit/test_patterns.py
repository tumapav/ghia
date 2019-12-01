from ghia import ghia_patterns
from ghia import ghia_issue
from tests.unit.helpers import get_config_object, get_issue
import pytest
import click


@pytest.fixture
def issue1_fixture():
    return get_issue('issue1.json')


@pytest.fixture
def issue2_empty():
    return get_issue('issue2.empty.json')


@pytest.fixture
def rules_config_1():
    return get_config_object('rules.sample.cfg')


@pytest.fixture
def rules_config_2():
    return get_config_object('rules.sample2.cfg')


@pytest.fixture
def rules_config_no_fallback():
    return get_config_object('rules.no-fallback.cfg')


@pytest.fixture
def rules_config_only_fallback():
    return get_config_object('rules.only-fallback.cfg')


def test_pattern_error_wrong_syntax():
    """ Test wrong syntax, of the pattern definition user:regex"""
    with pytest.raises(click.BadParameter) as e:
        p = ghia_patterns.Pattern("title")
    assert str(e.value) == "incorrect configuration format"
    with pytest.raises(click.BadParameter):
        p = ghia_patterns.Pattern("")


def test_pattern_error_wrong_type():
    """ Test non existent pattern type """
    with pytest.raises(click.BadParameter) as e:
        p = ghia_patterns.Pattern("invalid:type")
    assert str(e.value) == "incorrect configuration format"


def test_pattern_error_invalid_regex():
    """ Test invalid regex """
    with pytest.raises(click.BadParameter) as e:
        p = ghia_patterns.Pattern("title:.**")
    assert str(e.value) == "incorrect configuration format"


@pytest.mark.parametrize(
    ['res', 'pattern_str'],
    [(True,  "title:Found"),
     (True,  "title:.*"),
     (False, "title:x"),
     (False, "title:a bug.+"),
     (True,  "text:having a problem"),
     (False, "text:x"),
     (False, "text:a bug.+"),
     (True,  "text:.*"),
     (True,  "label:bug"),
     (True,  "label:bu.*"),
     (False, "label:a bug.+"),
     (False, "label:x"),
     (True,  "any:^bug$"),
     (True,  "any:having a problem"),
     (True,  "any:Found"),
     (False, "any:a bug.+")],
)
def test_pattern_match_title(issue1_fixture, pattern_str, res):
    """ Test pattern matching with different pattern types """
    issue = ghia_issue.Issue(issue1_fixture)
    p = ghia_patterns.Pattern(pattern_str)
    assert res == bool(p.match(issue))


@pytest.mark.parametrize(
    ['res', 'username'],
    [(True,  "test"),
     (True,  "test.test"),
     (True,  "test32"),
     (True,  "test-test"),
     (False,  "test#re"),
     (False, "ťěšť"),
     (False, "5%"),
     (False, "=test")],
)
def test_ghiapatterns_validate_username(rules_config_1, res, username):
    """ Test github username validation """
    g = ghia_patterns.GhiaPatterns(rules_config_1)
    if res:
        g.validate_username(username)
    else:
        with pytest.raises(click.BadParameter) as e:
            g.validate_username(username)
        assert str(e.value) == "incorrect configuration format"


def test_issue_init(rules_config_1):
    g = ghia_patterns.GhiaPatterns(rules_config_1)
    assert g.fallback == "Need assignment"
    assert len(g.patterns) == 2
    assert len(g.patterns["tumapav"]) == 5
    assert len(g.patterns["octocat"]) == 1


def test_issue_init_no_fallback(rules_config_no_fallback):
    g = ghia_patterns.GhiaPatterns(rules_config_no_fallback)
    assert g.fallback is None


def prepare_patterns(rules_config, issue_fixture, strategy = "append"):
    g = ghia_patterns.GhiaPatterns(rules_config)
    g.strategy = strategy
    issue = ghia_issue.Issue(issue_fixture)
    res = g.apply_to(issue)
    return res, issue


def test_apply_patterns_no_change(rules_config_1, issue1_fixture):
    res, issue = prepare_patterns(rules_config_1, issue1_fixture)
    assert res is None


def test_apply_patterns_fallback(rules_config_only_fallback, issue2_empty):
    res, issue = prepare_patterns(rules_config_only_fallback, issue2_empty)
    assert res is not None
    assert res.assignees == set()
    assert res.labels == {'Need assignment'}


def test_apply_patterns_strategy_change(rules_config_2, issue1_fixture):
    res, issue = prepare_patterns(rules_config_2, issue1_fixture, "change")
    assert res is not None
    assert res.assignees == set(['octocat','tumapav'])
    assert res.labels == {'bug'}


def test_apply_patterns_strategy_change_no_changes(rules_config_1, issue1_fixture):
    res, issue = prepare_patterns(rules_config_1, issue1_fixture, "change")
    assert res is None


def test_apply_patterns_strategy_set(rules_config_2, issue2_empty):
    res, issue = prepare_patterns(rules_config_2, issue2_empty, "set")
    assert res is not None
    assert res.assignees == set(['tumapav'])
    assert res.labels == set()


def test_apply_patterns_strategy_set_no_change(rules_config_2, issue1_fixture):
    res, issue = prepare_patterns(rules_config_2, issue1_fixture, "set")
    assert res is None


def test_apply_patterns_strategy_append_no_change(rules_config_2, issue1_fixture):
    res, issue = prepare_patterns(rules_config_2, issue1_fixture, "set")
    assert res is None


def test_apply_patterns_strategy_append(rules_config_2, issue1_fixture):
    res, issue = prepare_patterns(rules_config_2, issue1_fixture, "append")
    assert res is not None
    assert res.assignees == set(['tumapav','octocat'])
    assert res.labels == set(['bug'])


def test_apply_patterns_strategy_append_no_match(rules_config_1, issue2_empty):
    res, issue = prepare_patterns(rules_config_1, issue2_empty, "append")
    assert res is not None
    assert res.assignees == set()
    assert res.labels == set(['Need assignment'])
