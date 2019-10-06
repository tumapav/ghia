import click


@click.command()
@click.argument('reposlug')
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
def hello(reposlug, strategy, dry_run, config_auth, config_rules):
    """CLI tool for automatic issue assigning of GitHub issues"""
    pass


if __name__ == '__main__':
    hello()
