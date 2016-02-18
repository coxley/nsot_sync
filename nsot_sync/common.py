from __future__ import print_function
import click


def error(msg):
    click.secho('ERROR: %s' % msg, fg='red', err=True)


def info(msg):
    click.secho('INFO: %s' % msg, fg='blue', err=True)


def success(msg):
    click.secho('SUCCESS: %s' % msg, fg='green', err=True)
