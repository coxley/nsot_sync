from __future__ import print_function
from nsot_sync.drivers.base_driver import BaseDriver
import socket
import platform
import netifaces


class SimpleDriver(BaseDriver):
    '''Simple driver

    This driver will collect network information via netifaces on the localhost
    then generate NSoT resources for them and the host. The only attribute
    created and applied is 'desc'.

    If you're writing a driver to supplement just attributes, consider
    subclassing this class to get the localhost network data.
    '''

    REQUIRED_ATTRS = [
        {
            'name': 'desc',
            'resource_name': 'Device',
            'description': 'Description',
            'display': True,
            'required': False,
        },
        {
            'name': 'desc',
            'resource_name': 'Network',
            'description': 'Description',
            'display': True,
            'required': False,
        },
        {
            'name': 'desc',
            'resource_name': 'Interface',
            'description': 'Description',
            'display': True,
            'required': False,
        }
    ]
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
        resources_to_create = {}
        resources_to_create.update(self.get_networks_and_interfaces())
        resources_to_create.update({'devices': [self.get_device()]})
        return resources_to_create

    def get_networks_and_interfaces(self):  # -> Dict[string, list]
        '''Returns dict of interfaces and networks

        Uses netifaces to get AF_INET, AF_INET6, and AF_LINK
        '''
        self.logger.debug('Grabbing interfaces from netifaces')
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
            self.logger.debug('Iteration %s of prospecting interfaces', intf)
            for net_resources, intf_resource in self.intf_fetch(intf):
                networks.extend(net_resources)
                interfaces.append(intf_resource)

        return {'interfaces': interfaces, 'networks': networks}

    def get_device(self):  # -> Dict[string, list]
        '''Returns dict keyed to devices'''
        self.logger.debug('Creating resource for device')
        return {
            'hostname': socket.gethostname().split('.')[0],
        }

    def intf_fetch(self, ifname):
        '''Return tuple of networks (list) and interface resource (dict)

        To clarify, this is looking at the possibly many address families for a
        single interface and returning the resources to create the networks and
        then the single interface.
        '''
        families = netifaces.ifaddresses(ifname)
        try:
            # Not all interfaces have AF_LINK
            mac_addr = families[netifaces.AF_LINK][0]['addr']
        except KeyError:
            mac_addr = '00:00:00:00:00:00'
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
                        'site_id': self.site_id,
                        'state': 'assigned',
                        'prefix_length': length,
                        'attributes': {
                            'desc': '%s on %s' % (ifname, platform.node()),
                        }
                    }
                    networks.append(network_resource)

        interface = {
            'addresses': ['%s/%s' % (r['network_address'], r['prefix_length'])
                          for r in networks],
            'description': '%s on %s' % (ifname, platform.node()),
            'mac_address': mac_addr,
            'device': socket.gethostname().split('.')[0],
            'attributes': {},
            'type': 6,
            'name': ifname
        }
        return [(networks, interface)]
