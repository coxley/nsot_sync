from __future__ import print_function
import json
import subprocess
from nsot_sync.common import error
from nsot_sync.drivers.simple import SimpleDriver


class FacterDriver(SimpleDriver):
    '''Facter Driver

    This driver supplements SimpleDriver's localhost information fetching with
    attributes gathered from facter

    Facter is required to be installed to use this
    '''
    REQUIRED_ATTRS = []

    def get_resources(self):  # -> Dict[string, list]
        return {
            'networks': [],
            'devices': [],
            'interfaces': [],
        }

    def get_facter_results(self, cmd='facter -p --json'):  # -> Dict[str, Any]
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
