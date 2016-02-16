import click


@click.command()
@click.pass_context
def cli(ctx):
    '''The facter driver can add attributes to created resources from facter'''
    click.secho('Using driver: facter', fg='green')
