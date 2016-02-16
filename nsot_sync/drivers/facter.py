from __future__ import print_function
import json
import subprocess
from nsot_sync.common import error


def main(r_types):
    return get_facter_results()


def get_facter_results(cmd='facter -p --json'):  # -> Dict[str, Any]
    spawn = subprocess.Popen(
        cmd.split(),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    result, err = spawn.communicate()

    if err:
        error(err)

    return json.loads(result)
