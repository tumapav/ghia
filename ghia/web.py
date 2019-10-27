import click
import configparser
import hmac
import os
from flask import Flask
from flask import request
from flask import render_template
from .ghia_patterns import GhiaPatterns
from .ghia_requests import GhiaRequests
from .ghia_issue import Issue


def create_app(conf):
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
        secret = None
    else:
        secret = config["github"]["secret"]

    token = config["github"]["token"]
    ghia_patterns = GhiaPatterns(config)
    ghia_patterns.set_strategy('append')

    req = GhiaRequests(token)
    user = req.get_user()

    def github_verify_request():
        github_signed = request.headers.get('X-Hub-Signature')
        if github_signed is None and secret is None:
            # Signature check is skipped only if the secret is missing in the ghia-config and in the webhook config
            return True
        elif github_signed is None or secret is None:
            # GitHub request has signature but ghia-config is missing the secret
            # or ghia-config has secret but webhook doesn't send signed request
            raise ValueError("Signature verification failed.")

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

        if data["issue"]["state"] == "closed":
            return "Closed issue is ignored."

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
