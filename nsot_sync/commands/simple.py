from __future__ import print_function
import click
from nsot_sync.drivers import simple


@click.command()
@click.pass_context
def cli(ctx):
    '''Simple driver uses system interfaces to generate NSoT resources

    No extra attributes are added to the resources other than linking them
    together
    '''

    driver = simple.SimpleDriver(click_ctx=ctx)
    if ctx.obj['NOOP']:
        driver.noop()
        return

    driver.handle_resources()
