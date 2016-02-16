from __future__ import print_function
import json
from abc import abstractmethod
from pynsot.client import get_api_client
from nsot_sync.common import error, info


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

    def ensure_attrs(self):
        '''Ensure that attributes from REQUIRED_ATTRS exist, don't overwrite'''
        for attr in self.REQUIRED_ATTRS:
            # Loop through each attribute to create. Once #142 is fixed, this
            # might be able to be done in bulk
            attr.update({'site_id': self.site_id})

            try:
                self.client.attributes.post(attr)
            except Exception as e:
                if e.response.status_code == 500:
                    # Because of NSoT issue #142, duplicate resources return
                    # HTTP 500. Seems to be because the error isn't returned as
                    # serializable JSON on the backend.
                    #
                    # https://github.com/dropbox/nsot/issues/142
                    info(
                        'Adding attribute "%s" returned 500, likely a dup' %
                        (attr['name'])
                    )
                    pass
                else:
                    self.handle_pynsot_err(e)

    def handle_pynsot_err(self, e):
        content = json.dumps(e.content)
        error(content)
