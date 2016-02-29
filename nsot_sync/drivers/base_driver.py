from __future__ import print_function
import re
import json
import click
import logging
from abc import abstractmethod
from requests.exceptions import ConnectionError
from pynsot.client import get_api_client
from pynsot.vendor.slumber.exceptions import HttpClientError
from nsot_sync.common import success


class BaseDriver(object):
    '''Base class for nsot_sync drivers

    This is meant for subclassing and you must override .get_resources() which
    should return resources to create, keyed by the resource type.

    >>> self.get_resources()
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

    Attributes:
        click_ctx (click.Context): Click context
        site_id (int): NSoT site id to perfom operations on
        client (pynsot.EmailHeaderClient): via pynsot.client.get_api_client()
        logger (Logger): logging.getLogger(__name__)
        REQUIRED_ATTRS (list): If you're driver sets attributes, you can't
            guarantee the remote end will have these set up. To get around
            this, override the REQUIRED_ATTRS property. This should be a list
            of NSoT attribute dicts. If you're not familiar with the format,
            see the below examples:

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

    Args:
        click_ctx (click.Context): Context from Click. Context.obj values are
            manually set to share throughout the context at the entrypoint
            functions. Any that need sharing are probably passed by the main
            one (noop, site_id, etc) but when subclassing you know your driver
            best

            Also helps with doing CLI exits like click_ctx.fail(msg)
    '''

    REQUIRED_ATTRS = []

    def __init__(self, click_ctx=None):
        '''
        '''

        if click_ctx is None:
            raise Exception('Please pass click context to driver init')

        self.click_ctx = click_ctx
        self.site_id = click_ctx.obj['SITE_ID']
        self.client = get_api_client()
        logger = logging.getLogger(__name__)
        self.logger = logger

        self.require_extra_attrs()

    @abstractmethod
    def get_resources(self):
        pass

    def require_extra_attrs(self):
        '''Appends EXTRA_ATTRS to REQUIRED_ATTRS so they're ensured

        Note:
            These come from the CLI args --[resource]-attrs
        '''
        extra = self.click_ctx.obj['EXTRA_ATTRS']
        for rtype, resources in extra.iteritems():
            rname = re.match('(?P<resource>\S+)_attrs', rtype).groups()[0]
            for name in resources.keys():
                resource = {
                    'name': name,
                    'resource_name': rname.title(),
                    'required': False,
                }
                self.REQUIRED_ATTRS.append(resource)

    def add_extra_attrs(self, resources):
        '''Updates resources with relevant extra attrs given at the CLI

        Note:
            This happens right before resources are either created or No-Op'd

        Args:
            resources (dict): Resources as returned by self.get_resources
        '''
        extra = self.click_ctx.obj['EXTRA_ATTRS']
        r = resources
        self.logger.debug('Extra: %s', extra)

        for rtype, attrs in extra.iteritems():
            rname_pl = '%ss' % re.match('(\S+)_attrs', rtype).groups()[0]
            [x['attributes'].update(attrs) for x in r[rname_pl]]

        return r

    def noop(self):
        '''Outputs JSON to STDOUT of the resources that would be created'''
        click.echo(json.dumps(self.merge_all()))

    def merge_all(self):
        '''Merge all resources, adding extra attrs, for what will be created

        This is useful for representing what exactly will be created and lets
        .noop() be less redundant

        Returns:
            dict: Same format as would be expected from .get_resources
        '''
        from_driver = self.get_resources()
        extra_attrs_added = self.add_extra_attrs(from_driver)
        return extra_attrs_added

    def handle_resources(self):
        '''Takes output of .get_resources to create/update as needed'''
        resources = self.merge_all()
        self.logger.debug('All staged resources: %s', resources)

        # Create resources, interfaces last so networks and device exist to
        # attach to
        [self.handle_device(device) for device in resources['devices']]
        [self.handle_network(network) for network in resources['networks']]
        [self.handle_interface(interface)
         for interface in resources['interfaces']]

    def handle_network(self, network):
        '''Take a single network and create/update in NSoT'''

        c = self.client
        cidr = '%s/%d' % (network['network_address'], network['prefix_length'])
        network.update({'site_id': self.site_id})
        self.logger.debug('Network: %s', network)
        already_exists = False
        try:
            # Test if existing network to determine whether to PATCH or POST
            # Remove attributes since these may not match exactly and the point
            # is to be updating them
            lookup = network.copy()
            lookup.pop('attributes', None)
            self.logger.debug('Lookup metadata: %s', lookup)
            existing = c.networks.get(**lookup)['data']['networks']
            self.logger.debug('Existing networks: %s', existing)
            if existing:
                already_exists = True
        except ConnectionError:
            self.click_ctx.fail('Cannot connect to NSoT server')
        except HttpClientError as e:
            self.handle_pynsot_err(e)
        except Exception as e:
            self.logger.exception('handle_network, checking for existing net')

        if already_exists:
            # Set the proper ID to PATCH
            network['id'] = existing[0]['id']
            try:
                self.logger.info('Patching: %s', network)
                c.networks.patch([network])
                success('%s updated!' % cidr)
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e, cidr)
            except Exception as e:
                self.logger.exception('handle_network, patching network')
        else:
            try:
                self.logger.info('Posting: %s', network)
                c.networks.post(network)
                success('%s created!' % cidr)
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e, cidr)
            except Exception as e:
                self.logger.exception('handle_network, posting network')

    def handle_interface(self, interface):
        '''Take a single interface and create/update in NSoT

        Note:
            As part of the driver contract, an interface passed here might have
            'device' set to a hostname instead of the ID. Until NSoT supports
            natural key references within a resource, we should detect and
            fetch this
        '''
        c = self.client
        name = interface['name']
        device = interface['device']
        interface.update({'site_id': self.site_id})
        self.logger.debug('Interface: %s', interface)
        try:
            result = c.devices.get(hostname=interface['device'])
            if result['data']['total'] == 0:
                raise ValueError
            else:
                interface['device'] = result['data']['devices'][0]['id']
        except ValueError:
            interface['device'] = int(interface['device'])
        except Exception as e:
            self.logger.exception('handle_interface, setting device ID')

        already_exists = False
        try:
            # Test if existing interface to determine whether to PATCH or POST
            # Remove attributes since these may not match exactly and the point
            # is to be updating them
            lookup = interface.copy()
            lookup.pop('attributes', None)
            self.logger.debug('Lookup metadata: %s', lookup)
            existing = c.interfaces.get(**lookup)['data']['interfaces']
            self.logger.debug('Existing interface: %s', existing)
            if existing:
                already_exists = True
        except ConnectionError:
            self.click_ctx.fail('Cannot connect to NSoT server')
        except HttpClientError as e:
            self.handle_pynsot_err(e)
        except Exception as e:
            self.logger.exception('handle_interface, checking for existing')

        if already_exists:
            # Set the proper ID to PATCH
            interface['id'] = existing[0]['id']
            try:
                self.logger.info('Patching: %s', interface)
                c.interfaces.patch([interface])
                success('%s:%s updated!' % (device, name))
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e, name)
            except Exception as e:
                self.logger.exception('handle_interface, patching interface')
        else:
            try:
                self.logger.info('Posting: %s', interface)
                c.interfaces.post(interface)
                success('%s:%s created!' % (device, name))
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e, name)
            except Exception as e:
                self.logger.exception('handle_interface, posting interface')

    def handle_device(self, device):
        '''Take a single device and create/update in NSoT'''

        c = self.client
        device.update({'site_id': self.site_id})
        self.logger.debug('Device', device)
        already_exists = False
        try:
            lookup = device.copy()
            lookup.pop('attributes', None)
            self.logger.debug('Lookup metadata: %s', lookup)
            existing = c.devices.get(**lookup)['data']['devices']
            self.logger.debug('Existing devices: %s', existing)
            if existing:
                already_exists = True
        except ConnectionError:
            self.click_ctx.fail('Cannot connect to NSoT server')
        except HttpClientError as e:
            self.handle_pynsot_err(e)
        except Exception as e:
            self.logger.exception('handle_device, checking for existing dev')

        if already_exists:
            device['id'] = existing[0]['id']
            try:
                self.logger.info('Patching: %s', device)
                c.devices.patch([device])
                success('%s updated!' % device['hostname'])
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e, device['hostname'])
            except Exception as e:
                self.logger.exception('handle_device, patching device')
        else:
            try:
                self.logger.info('Posting: %s', device)
                c.devices.post(device)
                success('%s created!' % device['hostname'])
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e, device['hostname'])
            except Exception as e:
                self.logger.exception('handle_device, posting device')

    def ensure_attrs(self):
        '''Ensure that attributes from REQUIRED_ATTRS exist, don't overwrite'''
        c = self.client
        for attr in self.REQUIRED_ATTRS:
            # Loop through each attribute to create. Once #142 is fixed, this
            # might be able to be done in bulk
            attr.update({'site_id': self.site_id})
            try:
                existing = c.attributes.get(**attr)['data']['attributes']
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e)
            except Exception as e:
                self.logger.exception('ensure_attrs, finding exist %s' % attr)

            try:
                if existing:  # Like in the docstring, don't overwrite
                    msg = 'Attribute %s exists, not overwriting'
                    self.logger.info(msg, attr['name'])
                else:
                    self.logger.info('Posting attribute %s', attr['name'])
                    c.attributes.post(attr)
                    success('%s created!' % attr['name'])
            except ConnectionError:
                self.click_ctx.fail('Cannot connect to NSoT server')
            except HttpClientError as e:
                self.handle_pynsot_err(e)
            except Exception as e:
                self.logger.exception('ensure_attrs, posting attr %s' % attr)

    def handle_pynsot_err(self, e, desc=''):
        base_net = "IP Address needs base network"
        if base_net in e.content:
            self.logger.warning(
                '%s: No base network created for relevant resource',
                desc
            )
            return
        content = json.dumps(e.content)
        if desc:
            content = '%s: %s' % (desc, content)
        # error(content)
        self.logger.error(content)
