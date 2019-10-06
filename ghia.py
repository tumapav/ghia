import click
import re


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

    return True


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
              type=click.File('r'))
@click.option('-r', '--config-rules',
              metavar='FILENAME',
              help='File with assignment rules configuration.',
              required=True,
              type=click.File('r'))
def ghia(reposlug, strategy, dry_run, config_auth, config_rules):
    """CLI tool for automatic issue assigning of GitHub issues"""
    pass


if __name__ == '__main__':
    ghia()
