import click
from click.testing import CliRunner
from nsot_sync.cli import cli


def test_basic_exec():
    runner = CliRunner()
    results = {
        'main_help': runner.invoke(cli, ['--help']),
        'simple_help': runner.invoke(cli, ['--help', 'simple']),
        'facter_help': runner.invoke(cli, ['--help', 'facter']),
    }
    exit_codes = set(result.exit_code for result in results.values())
    all_zero = len(exit_codes) == 1 and 0 in exit_codes
    assert all_zero
