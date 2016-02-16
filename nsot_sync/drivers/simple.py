from __future__ import print_function
from nsot_sync.drivers.base_driver import BaseDriver
import platform
import netifaces


class SimpleDriver(BaseDriver):
    '''Simple driver

    This driver will collect network information via netifaces on the localhost
    then generate NSoT resources for them and the host. No extra attributes
    will be created/applied.

    If you're writing a driver to supplement just attributes, consider
    subclassing this class to get the localhost network data.
    '''

    INTF_IGNORE_PREFIXES = [
        'lo',
        'docker',
        'fw0',
    ]
    INTF_OK_FAMILIES = [
        netifaces.AF_INET,
        netifaces.AF_INET6,
        netifaces.AF_LINK,
    ]

    def get_resources(self):  # -> Dict[string, list]
        return self.get_networks_and_interfaces()

    def get_networks_and_interfaces(self):  # -> Dict[string, list]
        '''Returns dict of interfaces and networks

        Uses netifaces to get AF_INET, AF_INET6, and AF_LINK
        '''
        prospects = [intf for intf in netifaces.interfaces()
                     if not intf.startswith(tuple(self.INTF_IGNORE_PREFIXES))]

        networks = []
        interfaces = []
        for intf in prospects:
            # This loop is a bit weird, but an interface can have many
            # addresses of many address families.
            #
            # This loops through prospecting interfaces, fetching all the
            # possible network resources you can create from it and the
            # interface resource itself.
            for net_resources, intf_resource in self.intf_fetch(intf):
                networks.extend(net_resources)
                interfaces.append(intf_resource)

        return {'interfaces': interfaces, 'networks': networks}

    def get_devices(self):  # -> Dict[string, list]
        '''Returns dict keyed to devices'''
        pass

    def intf_fetch(self, ifname):
        '''Return tuple of networks (list) and interface resource (dict)

        To clarify, this is looking at the possibly many address families for a
        single interface and returning the resources to create the networks and
        then the single interface.
        '''
        families = netifaces.ifaddresses(ifname)
        mac_addr = families[netifaces.AF_LINK][0]['addr']
        networks = []

        for family, addrs in families.iteritems():
            # Loop through all address families, creating network resources
            # from the ones we care about
            if family not in self.INTF_OK_FAMILIES:
                continue

            if family in (netifaces.AF_INET, netifaces.AF_INET6):
                # If needed to quickly do IPv6 prefix length, below might help
                # 16 * len(filter(None, a.split(':'))) for ffff:: netmask
                for addr in addrs:
                    length = family == netifaces.AF_INET and 32 or 128
                    if family == netifaces.AF_INET6:
                        addr['addr'] = addr['addr'].split('%')[0]
                    network_resource = {
                        'is_ip': True,
                        'network_address': addr['addr'],
                        'site_id': self.cli_params['SITE_ID'],
                        'state': 'assigned',
                        'prefix_length': length,
                        'attributes': {},
                    }
                    networks.append(network_resource)

        interface = {
            'addresses': ['%s/%s' % (r['network_address'], r['prefix_length'])
                          for r in networks],
            'description': '%s on %s' % (ifname, platform.node()),
            'mac_address': mac_addr,
            'device': None,
            'attributes': {},
            'type': 6,
            'name': ifname
        }
        return [(networks, interface)]
