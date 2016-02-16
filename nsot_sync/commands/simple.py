from __future__ import print_function
import json
import click
from nsot_sync.drivers import simple_driver


@click.command()
@click.pass_context
def cli(ctx):
    '''Simple driver uses system interfaces to generate NSoT resources

    No extra attributes are added to the resources other than linking them
    together
    '''
    driver = simple_driver.SimpleDriver(cli_params=ctx.obj)
    if ctx.obj['NOOP']:
        click.echo(json.dumps(driver.get_resources()))
        return

    driver.ensure_attrs()