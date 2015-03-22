from base_test import BaseServerTestCase
from cloudify_rest_client.exceptions import CloudifyClientError


class SecurityTestCase(BaseServerTestCase):

    def setUp(self):
        self._secured = True
        super(SecurityTestCase, self).setUp()

    def test_secured_client(self):
        client = self.create_client(user='user1', password='pass1')
        parameters = {'param1': 'val1', 'param2': 'val2'}
        execution = client.executions.start(11,
                                            'install',
                                            parameters,
                                            allow_custom_parameters=True)
        client.executions.list()

    def test_wrong_credentials(self):
        client = self.create_client(user='user1', password='pass2')
        self.assertRaises(CloudifyClientError, client.deployments.list)

    def test_missing_credentials(self):
        client = self.create_client()
        self.assertRaises(CloudifyClientError, client.deployments.list)

    def test_missing_user(self):
        client = self.create_client(password='pass1')
        self.assertRaises(CloudifyClientError, client.deployments.list)

    def test_missing_password(self):
        client = self.create_client(user='user1')
        self.assertRaises(CloudifyClientError, client.deployments.list)

    '''
    def tearDown(self):
        self._secured = True
        super(SecurityTestCase, self).tearDown()
    '''
