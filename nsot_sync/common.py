from __future__ import print_function
import click


def error(msg):
    click.secho('ERROR: %s' % msg, fg='red', err=True)


def info(msg):
    click.secho('INFO: %s' % msg, fg='blue', err=True)


def success(msg):
    click.secho('SUCCESS: %s' % msg, fg='green', err=True)


def validate_csv(ctx, param, value):
    '''List must be passed as comma separated values

    Having spaces after the comma is fine:

        eth0,eth1, eth2,eth3
        eth,lo, docker,vpn
    '''
    import re

    if not value:
        return []

    try:
        ifnames = re.split(',|, ', value)
        return ifnames
    except:
        raise click.BadParameter(validate_csv.__doc__)
