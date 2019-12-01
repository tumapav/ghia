from ghia import ghia_patterns
from ghia import cli
from tests.unit.helpers import fixtures_path
import pytest
import click
import configparser
import flexmock


def get_config_string(name):
    config = configparser.ConfigParser()
    config.optionxform = str
    with open(fixtures_path() + name) as f:
        s = f.read()
    return s


@pytest.fixture
def credentials_config_1():
    return get_config_string('credentials.sample.cfg')


@pytest.fixture
def rules_config_1():
    return get_config_string('rules.sample.cfg')


@pytest.fixture
def rules_config_empty():
    return get_config_string('rules.empty.cfg')


@pytest.fixture
def rules_config_no_token():
    return get_config_string('rules.no-token.cfg')


def test_validate_credentials_file_empty(rules_config_empty):
    value = flexmock(read=lambda: rules_config_empty)

    with pytest.raises(click.BadParameter) as e:
        cli.validate_credentials_file(None, None, value)
    assert str(e.value) == "incorrect configuration format"


def test_validate_credentials_file_no_token(rules_config_no_token):
    value = flexmock(read=lambda: rules_config_no_token)

    with pytest.raises(click.BadParameter) as e:
        cli.validate_credentials_file(None, None, value)
    assert str(e.value) == "incorrect configuration format"


def test_validate_credentials_file(credentials_config_1):
    value = flexmock(read=lambda: credentials_config_1)

    res = cli.validate_credentials_file(None, None, value)
    assert res == "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def test_validate_config_file_empty(rules_config_empty):
    value = flexmock(read=lambda: rules_config_empty)

    with pytest.raises(click.BadParameter) as e:
        cli.validate_config_file(None, None, value)
    assert str(e.value) == "incorrect configuration format"


def test_validate_config_file(rules_config_1):
    value = flexmock(read=lambda: rules_config_1)

    res = cli.validate_config_file(None, None, value)
    assert isinstance(res, ghia_patterns.GhiaPatterns)
    assert len(res.patterns) == 2
    assert len(res.patterns["tumapav"]) == 5
    assert len(res.patterns["octocat"]) == 1
