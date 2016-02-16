from __future__ import print_function
import json
from abc import abstractmethod
from pynsot.client import get_api_client
from nsot_sync.common import error, success


class BaseDriver(object):
    '''Base class for nsot_sync drivers

    This is meant for subclassing and you must override .get_resources()

    If you're driver sets attributes, you can't guarantee the remote end will
    have these set up. To get around this, override the REQUIRED_ATTRS
    property. This should be a list of NSoT attribute dicts. If you're not
    familiar with the format, see the below examples:

    >>> REQUIRED_ATTRS = [
            {
                'name': 'dc',
                'resource_name': 'Device',
                'description': 'Datacenter',
                'display': True,
                'required': True,
                'multi': False,
            }
        ]

    '''

    REQUIRED_ATTRS = []

    def __init__(self, cli_params=None):
        '''

        :param cli_params: Parameters passed into click (eg, ctx.obj)
        :type cli_params: dict

        ctx.obj values are manually set to share throughout the context at the
        entrypoint functions. Any that need sharing are probably passed by the
        main one (noop, site_id, etc) but when subclassing you know your driver
        best
        '''

        if cli_params is None:
            raise Exception('Please pass ctx.obj to driver init')

        self.cli_params = cli_params
        self.site_id = cli_params['SITE_ID']
        self.client = get_api_client()

    @abstractmethod
    def get_resources(self):
        pass

    def handle_resources(self):
        '''Takes output of .get_resources to create/update as needed'''
        resources = self.get_resources()

        # Create resources, interfaces last so networks and device exist to
        # attach to
        # [self.handle_device(device) for device in resources['devices']]
        [self.handle_network(network) for network in resources['networks']]
        # [self.handle_interface(interface)
        #  for interface in resources['interfaces']]

    def handle_network(self, network):
        '''Take a network and create/update in NSoT'''

        # Because of issue #36 and #118 upstream NSoT, as of this comment
        # resources are not round-tripable. This means that "cidr" is a
        # required field for creating a network resource, but not what is used
        # to represent it
        #
        # To support the round-tripable future, this function will take a
        # future-proofed network_addriss+length resource and add cidr to it
        # when creating
        c = self.client
        cidr = '%s/%s' % (network['network_address'], network['prefix_length'])
        network['cidr'] = cidr
        try:
            existing = c.networks.query.get(**network)['data']['networks']
        except Exception as e:
            self.handle_pynsot_err(e)

        if existing:
            network['id'] = existing[0]['id']
            try:
                c.networks.put(network)
                success('%s updated!' % cidr)
            except Exception as e:
                self.handle_pynsot_err(e, cidr)
        else:
            try:
                c.networks.post(network)
                success('%s created!' % cidr)
            except Exception as e:
                self.handle_pynsot_err(e, cidr)

    def handle_interface(self, interface):
        pass

    def handle_device(self, device):
        pass

    def ensure_attrs(self):
        '''Ensure that attributes from REQUIRED_ATTRS exist, don't overwrite'''
        c = self.client
        for attr in self.REQUIRED_ATTRS:
            # Loop through each attribute to create. Once #142 is fixed, this
            # might be able to be done in bulk
            attr.update({'site_id': self.site_id})
            try:
                existing = c.attributes.get(**attr)['data']['attributes']
            except Exception as e:
                self.handle_pynsot_err(e)

            try:
                if existing:  # Like in the docstring, don't overwrite
                    pass
                else:
                    self.client.attributes.post(attr)
                    success('%s created!' % attr['name'])
            except Exception as e:
                self.handle_pynsot_err(e)

    def handle_pynsot_err(self, e, desc=''):
        content = json.dumps(e.content)
        if desc:
            content = '%s: %s' % (desc, content)
        error(content)
