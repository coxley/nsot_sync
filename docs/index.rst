Welcome to NSoT_Sync
====================

Contents:

.. toctree::
   :maxdepth: 2

NSoT Sync is a program to help automate adding and updating resources in
`NSoT`_ from other sources. As of now, the main source is telling NSoT about
the running computer's networks, interfaces, and self but a WIP for syncing
from Solarwinds IPAM and SNMP is on the way.

.. _NSoT: https://github.com/dropbox/nsot

Motivations
-----------

NSoT as an IPAM is refreshing among the other open source solutions. Though to
see its potential, you generally need to write some code against it. The goal
of NSoT Sync is to provide those who want instant gratification with automatic
resource generation from a handful of common sources.

``nsot_sync`` is designed to be ran from cron or ad-hoc, to sync from remote or
local sources via built-in drivers.

Requirements
------------

* Python 2.7
* Functioning NSoT server
* Configured ``pynsotrc`` - See the `pynsot docs`_ or example config below
* ``jq`` is optional but very useful. Install it with ``apt-get install jq`` or
  ``pacman -S jq``

We try to maintain support across all Windows, OSX, and Linux computers. That
being said, we don't have any Windows systems to test on so there might be some
bugs there. If you run across one, please `submit an issue`_!

.. _submit an issue: https://github.com/coxley/nsot_sync/issues/new
.. _pynsot docs: https://github.com/dropbox/pynsot

Quickstart
----------

If you don't have an existing NSoT instance, do the following to get a working
instance and pynsot config:

.. code-block:: bash

    cat <<EOF > ~/.pynsotrc
    [pynsot]
    url = http://localhost:8990/api
    auth_method = auth_header
    auth_header = X-NSoT-Email
    default_site = 1
    email = nsot_sync@localhost
    default_domain = localhost
    EOF

    pip install nsot
    git clone https://github.com/dropbox/nsot
    cd nsot/demo && ./run_demo.sh


To finish bootstrapping, let's add a site/realm to store our resources and
install NSoT Sync:

.. code-block:: bash

    nsot sites add -n "My New Site"
    pip install nsot_sync

Running ``nsot_sync simple`` at this point should just work, but we'll run it
in No-Op mode first to see what will be created. ``jq`` is just used to
pretty-print the JSON output - completely optional.

.. code-block:: javascript

    $ nsot_sync --noop simple | jq .

    {
      "interfaces": [
        {
          "addresses": [
            "10.97.3.113/32",
            "fe80::82e6:50ff:fe0d:fc2e/128"
          ],
          "name": "wlp2s0",
          "mac_address": "80:e6:50:0d:fc:2e",
          "device": "coxley-mbp",
          "attributes": {},
          "type": 6,
          "description": "wlp2s0 on coxley-mbp"
        }
      ],
      "networks": [
        {
          "is_ip": true,
          "network_address": "10.97.3.113",
          "site_id": 1,
          "state": "assigned",
          "prefix_length": 32,
          "attributes": {
            "desc": "wlp2s0 on coxley-mbp"
          }
        },
        {
          "is_ip": true,
          "network_address": "fe80::82e6:50ff:fe0d:fc2e",
          "site_id": 1,
          "state": "assigned",
          "prefix_length": 128,
          "attributes": {
            "desc": "wlp2s0 on coxley-mbp"
          }
        }
      ],
      "devices": [
        {
          "attributes": {},
          "hostname": "coxley-mbp"
        }
      ]
    }

Now if we re-run this without ``--noop``, you should expect failures like::

    SUCCESS: coxley-mpb updated!
    2016-02-28 19:39:54 coxley-mpb nsot_sync.drivers.base_driver[7356] WARNING 10.97.3.113/32: No base network created for relevant resource
    2016-02-28 19:39:54 coxley-mpb nsot_sync.drivers.base_driver[7356] WARNING fe80::82e6:50ff:fe0d:fc2e/128: No base network created for relevant resource
    2016-02-28 19:39:54 coxley-mpb nsot_sync.drivers.base_driver[7356] WARNING wlp2s0: No base network created for relevant resource

This is side-effect of NSoT requiring a base subnet, of any size, for a host
address (/32 or /128) to be created. To remedy, we can add any parenting
subnet:

.. code-block:: bash

   $ nsot attributes add -n desc -d "Description" -r network
   $ nsot networks add -c 10.97.3.0/24 -a "desc=Guest wireless"
   $ nsot networks add -c fe80::/10 -a "desc=Link-local space"

   $ nsot_sync simple
   SUCCESS: coxley-mbp updated!
   SUCCESS: 10.97.3.113/32 created!
   SUCCESS: fe80::82e6:50ff:fe0d:fc2e/128 created!
   SUCCESS: coxley-mbp:wlp2s0 created!

   $ nsot networks list
   +------------------------------------------------------------------------------------------------------------------------------+
   | ID   Network                                   Prefix   Is IP?   IP Ver.   Parent ID   State       Attributes                |
   +------------------------------------------------------------------------------------------------------------------------------+
   | 1    10.97.3.0                                 24       False    4         None        allocated   desc=Guest wireless       |
   | 2    fe80:0000:0000:0000:0000:0000:0000:0000   10       False    6         None        allocated   desc=Link-local space     |
   | 3    10.97.3.113                               32       True     4         1           assigned    desc=wlp2s0 on coxley-mbp |
   | 4    fe80:0000:0000:0000:82e6:50ff:fe0d:fc2e   128      True     6         2           assigned    desc=wlp2s0 on coxley-mbp |
   +------------------------------------------------------------------------------------------------------------------------------+


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
