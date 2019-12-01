import betamax
import os
import configparser
import json


def fixtures_path():
    return os.path.dirname(os.path.realpath(__file__)) + '/fixtures/'


def get_config_object(name):
    config = configparser.ConfigParser()
    config.optionxform = str
    with open(fixtures_path() + name) as f:
        s = f.read()
    config.read_string(s)
    return config


def get_issue(name):
    with open(fixtures_path() + name) as f:
        s = f.read()
    return json.loads(s)


def betamax_setup():
    with betamax.Betamax.configure() as config:
        # where to find the cassettes
        config.cassette_library_dir = 'tests/unit/fixtures/cassettes'

        if 'GITHUB_TOKEN' in os.environ and 'GITHUB_REPO' in os.environ:
            TOKEN = os.environ['GITHUB_TOKEN']
            REPO = os.environ['GITHUB_REPO']
            if 'GITHUB_USER' in os.environ:
                USER = os.environ['GITHUB_USER']
            else:
                USER = ""  # not required for the application, only test
            config.default_cassette_options['record_mode'] = 'all'
        else:
            TOKEN = 'false_token'
            REPO = 'mi-pyt-ghia/tumapav'
            USER = 'tumapav'
            config.default_cassette_options['record_mode'] = 'none'

        # Set match strategy
        config.default_cassette_options['match_requests_on'].extend([
            'uri', 'method', 'body'
        ])

        # Hide the token in the cassettes
        config.define_cassette_placeholder('<TOKEN>', TOKEN)
    return TOKEN, REPO, USER
