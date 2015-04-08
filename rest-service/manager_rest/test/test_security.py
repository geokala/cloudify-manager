#########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from itsdangerous import base64_encode
from mock import patch

from cloudify_rest_client.exceptions import (CloudifyClientError,
                                             UnauthorizedError)

from base_test import BaseServerTestCase

CLOUDIFY_AUTH_HEADER = 'Authorization'
CLOUDIFY_AUTH_TOKEN_HEADER = 'Authentication-Token'


class SecurityTestBase(BaseServerTestCase):

    @staticmethod
    def create_auth_header(username=None, password=None, token=None):
        header = None
        # using or to allow testing of username without password and vice-versa
        if username or password:
            credentials = '{0}:{1}'.format(username, password)
            header = {CLOUDIFY_AUTH_HEADER: base64_encode(credentials)}
        elif token:
            header = {CLOUDIFY_AUTH_TOKEN_HEADER: token}

        return header

    def create_configuration(self):
        test_config = super(SecurityTestBase, self).create_configuration()
        test_config.secured_server = True

        test_config.securest_userstore_driver = {
            'implementation':
                'flask_securest.userstores.simple:SimpleUserstore',
            'properties': {
                'userstore': {
                    'user1': {
                        'username': 'user1',
                        'password': 'pass1',
                        'email': 'user1@domain.dom'
                    },
                    'user2': {
                        'username': 'user2',
                        'password': 'pass2',
                        'email': 'user2@domain.dom'
                    },
                    'user3': {
                        'username': 'user3',
                        'password': 'pass3',
                        'email': 'user3@domain.dom'
                    },
                },
                'identifying_attribute': 'username'
            }
        }
        test_config.auth_token_generator = {
            'implementation': 'flask_securest.authentication_providers.token:'
                              'TokenAuthenticator',
            'properties': {
                'secret_key': 'my_secret',
                'expires_in': 600
            }
        }
        test_config.securest_authentication_providers = [
            {
                'name': 'password',
                'implementation':
                    'flask_securest.authentication_providers.password'
                    ':PasswordAuthenticator',
                'properties': {
                    'password_hash': 'plaintext'
                }
            },
            {
                'name': 'token',
                'implementation': 'flask_securest.authentication_providers.'
                                  'token:TokenAuthenticator',
                'properties': {
                    'secret_key': 'my_secret'
                }
            }
        ]

        return test_config


class SecurityTest(SecurityTestBase):

    def test_secured_client(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='pass1'))
        client.deployments.list()

    def test_wrong_credentials(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='pass2'))
        self.assertRaises(UnauthorizedError, client.deployments.list)

    def test_missing_credentials(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username=None, password=None))
        self.assertRaises(UnauthorizedError, client.deployments.list)

    def test_missing_user(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username=None, password='pass1'))
        self.assertRaises(UnauthorizedError, client.deployments.list)

    def test_missing_password(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password=None))
        self.assertRaises(UnauthorizedError, client.deployments.list)

    def test_token_authentication(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='pass1'))
        token = client.tokens.get()
        client = self.create_client(SecurityTestBase.create_auth_header(
            token=token.value))
        client.blueprints.list()

    def test_secured_manager_blueprints_upload(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='pass1'))

        # the flask api client needs to be modified since it doesn't support
        # a bytes generator as "data" for file upload
        original_put = client._client.app.put

        def modified_put(*args, **kwargs):
            kwargs['data'] = kwargs['data'].next()
            return original_put(*args, **kwargs)

        with patch.object(client._client.app, 'put', modified_put):
            client.blueprints.upload(self.get_mock_blueprint_path(), 'bp-id')


class SecurityBypassTest(SecurityTestBase):

    BYPASS_PORT = 56789
    NOT_BYPASS_PORT = 56790

    def create_configuration(self):
        test_config = super(SecurityBypassTest, self).create_configuration()
        test_config.security_bypass_port = self.BYPASS_PORT
        return test_config

    def test_bypass_and_correct_credentials(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='pass1'))
        self._modify_client_to_pass_bypass_header(client, self.BYPASS_PORT)

        client.blueprints.list()

    def test_bypass_and_incorrect_password(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='wrong_pass'))
        self._modify_client_to_pass_bypass_header(client, self.BYPASS_PORT)

        client.blueprints.list()

    def test_bypass_and_nonexisting_user(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='nonexisting-user', password='pass1'))
        self._modify_client_to_pass_bypass_header(client, self.BYPASS_PORT)
        client.blueprints.list()

    def test_bypass_and_no_credentials(self):
        client = self.create_client()
        self._modify_client_to_pass_bypass_header(client, self.BYPASS_PORT)
        client.blueprints.list()

    def test_bypass_not_bypass_port_and_correct_credentials(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='pass1'))
        self._modify_client_to_pass_bypass_header(client,
                                                  self.NOT_BYPASS_PORT)
        client.blueprints.list()

    def test_bypass_not_bypass_port_and_incorrect_password(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='user1', password='wrong-pass'))
        self._modify_client_to_pass_bypass_header(client,
                                                  self.NOT_BYPASS_PORT)
        try:
            client.blueprints.list()
            self.fail('Call to blueprints list was successful despite using'
                      'incorrect password and not using the bypass port')
        except CloudifyClientError, e:
            self.assertEquals(401, e.status_code)

    def test_bypass_not_bypass_port_and_nonexisting_user(self):
        client = self.create_client(SecurityTestBase.create_auth_header(
            username='nonexisting-user', password='pass1'))
        self._modify_client_to_pass_bypass_header(client,
                                                  self.NOT_BYPASS_PORT)
        try:
            client.blueprints.list()
            self.fail('Call to blueprints list was successful despite using'
                      'nonexisting user and not using the bypass port')
        except CloudifyClientError, e:
            self.assertEquals(401, e.status_code)

    def test_bypass_not_bypass_port_and_no_credentials(self):
        client = self.create_client()
        self._modify_client_to_pass_bypass_header(client,
                                                  self.NOT_BYPASS_PORT)
        try:
            client.blueprints.list()
            self.fail('Call to blueprints list was successful despite using'
                      'no credentials and not using the bypass port')
        except CloudifyClientError, e:
            self.assertEquals(401, e.status_code)

    def _modify_client_to_pass_bypass_header(self, client, bypass_port):
        # making the given client use the bypass header on all requests
        orig_func = client._client._do_request

        def new_func(*args, **kwargs):
            headers = kwargs.get('headers', {})
            headers['X-Server-Port'] = bypass_port
            kwargs['headers'] = headers
            return orig_func(*args, **kwargs)

        client._client._do_request = new_func
