import click
import re
import configparser
import hmac
import os
from flask import Flask
from flask import request
from flask import render_template
from ghia_patterns import GhiaPatterns
from ghia_requests import GhiaRequests
from ghia_issue import Issue


def validate_credentials_file(ctx, param, value):
    config = configparser.ConfigParser()
    str_content = value.read()
    config.read_string(str_content)

    if "github" not in config or "token" not in config["github"]:
        raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    return config["github"]["token"]


def validate_config_file(ctx, param, value):
    config = configparser.ConfigParser()
    config.optionxform = str    # maintain case sensitivity in keys
    str_content = value.read()
    config.read_string(str_content)

    if "patterns" not in config:
        raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    return GhiaPatterns(config)


def validate_reposlug(ctx, param, value):
    _VALIDATION_ERR = "not in owner/repository format"

    # Check github name/repo format
    res = re.match('^[A-Za-z0-9.\-_]+/[A-Za-z0-9.\-_]+$', value)
    if res is None:
        raise click.BadParameter(_VALIDATION_ERR)

    parts = value.split("/")

    # Dot alone is a reserved name at github
    if parts[0] == "." or parts[1] == ".":
        raise click.BadParameter(_VALIDATION_ERR)

    return value


@click.command()
@click.argument('reposlug',
                callback=validate_reposlug,
                type=click.STRING)
@click.option('-s', '--strategy',
              help='How to handle assignment collisions.',
              type=click.Choice(['append', 'set', 'change']),
              default='append',
              show_default=True)
@click.option('-d', '--dry-run',
              is_flag=True,
              help='Run without making any changes.')
@click.option('-a', '--config-auth',
              metavar='FILENAME',
              help='File with authorization configuration.', required=True,
              type=click.File('r'),
              callback=validate_credentials_file)
@click.option('-r', '--config-rules',
              metavar='FILENAME',
              help='File with assignment rules configuration.',
              required=True,
              type=click.File('r'),
              callback=validate_config_file)
def ghia(reposlug, strategy, dry_run, config_auth, config_rules):
    """CLI tool for automatic issue assigning of GitHub issues"""

    token = config_auth
    ghia_patterns = config_rules
    ghia_patterns.set_strategy(strategy)
    ghia_patterns.set_dry_run(dry_run)

    req = GhiaRequests(token, reposlug)
    issues = req.get_issues()

    for issue in issues:
        updated_issue = ghia_patterns.apply_to(issue)
        if updated_issue and not dry_run:
            updated_issue = req.update_issue(updated_issue)
        ghia_patterns.print_report(issue, updated_issue)


def create_app():
    app = Flask(__name__)
    BAD_REQUEST = 400
    ALLOWED_ACTIONS = ["opened", "edited", "transferred", "reopened", "assigned", "unassigned", "labeled", "unlabeled"]

    env_conf = os.getenv('GHIA_CONFIG')
    if env_conf is None:
        raise click.BadParameter("GHIA_CONFIG is missing from the environment.")

    conf_paths = env_conf.split(":")
    config_content = ""
    for path in conf_paths:
        with open(path, 'r') as file:
            config_content += file.read() + "\n"

    config = configparser.ConfigParser()
    config.optionxform = str  # maintain case sensitivity in keys
    config.read_string(config_content)

    if "github" not in config or "token" not in config["github"]:
        raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    if "patterns" not in config:
        raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    if "secret" not in config["github"]:
        raise click.BadParameter("GitHub secret required for web version.")

    token = config["github"]["token"]
    secret = config["github"]["secret"]
    ghia_patterns = GhiaPatterns(config)
    ghia_patterns.set_strategy('append')

    req = GhiaRequests(token)
    user = req.get_user()

    def github_verify_request():
        github_signed = request.headers.get('X-Hub-Signature')
        if github_signed is None:
            # If the signature is missing from the request, user didn't configure it for the webhook
            return True

        try:
            hash_name, hash_value = github_signed.split('=', maxsplit=2)
        except ValueError:
            raise ValueError("Signature header has incorrect format.")

        if hash_name != 'sha1':
            raise ValueError("GitHub signatures are expected to use SHA1.")

        computed_hash = hmac.new(
            bytearray(secret, "utf-8"),    # get the secret as bytes
            digestmod='sha1',
            msg=request.get_data()
        )

        if computed_hash.hexdigest() != hash_value:
            raise RuntimeError("The request signature is wrong.")

    def process_issues():
        data = request.get_json(silent=True)
        if data is None:
            return "Webhook request missing JSON data.", BAD_REQUEST

        action = data["action"]
        if action not in ALLOWED_ACTIONS:
            return "This issue action is ignored."

        issue = Issue(data["issue"])
        req.slug = data["repository"]["full_name"]
        updated_issue = ghia_patterns.apply_to(issue)
        if updated_issue:
            req.update_issue(updated_issue)

        return "Issue update done."

    def process_webhook():
        event_type = request.headers.get('X-Github-Event')

        try:
            github_verify_request()
        except RuntimeError as e:
            return str(e), BAD_REQUEST

        if event_type == "issues":
            return process_issues()
        elif event_type == "ping":
            return "Ping OK"
        else:
            return "Event type ignored."

    @app.route('/', methods=['POST', 'GET'])
    def index():

        if request.method == 'POST':
            return process_webhook()

        return render_template('index.html', user=user, patterns=ghia_patterns)

    return app


if __name__ == '__main__':
    ghia()
