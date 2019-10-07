import click
import re
import configparser
from ghia_patterns import GhiaPatterns
from ghia_requests import GhiaRequests

def validate_credentials_file(ctx, param, value):
    config = configparser.ConfigParser()
    str_content = value.read()
    config.read_string(str_content)

    if "github" not in config or "token" not in config["github"]:
        raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    token = config["github"]["token"]
    return token


def validate_config_file(ctx, param, value):
    config = configparser.ConfigParser()
    str_content = value.read()
    config.read_string(str_content)

    if "patterns" not in config:
        raise click.BadParameter(GhiaPatterns.CONFIG_VALIDATION_ERR)

    gp = GhiaPatterns(config)
    gp.parse()

    return gp


def validate_reposlug(ctx, param, value):
    _VALIDATION_ERR = "not in owner/repository format"

    # Check github name/repo format
    res = re.match('^[A-Za-z0-9\.-_]+/[A-Za-z0-9\.-_]+$', value)
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
        if updated_issue:
            req.update_issue(updated_issue)

if __name__ == '__main__':
    ghia()
