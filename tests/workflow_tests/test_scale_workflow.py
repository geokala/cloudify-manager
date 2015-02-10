########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


from testenv import TestCase
from testenv.utils import get_resource as resource
from testenv.utils import deploy_application as deploy
from testenv.utils import execute_workflow


class TestScaleWorkflow(TestCase):

    def test_compute_scale_out_compute(self):
        expectations = self.deploy('scale1')
        expectations['compute']['new']['install'] = 1
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={'node_id': 'compute'})
        expectations['compute']['new']['install'] = 1
        expectations['compute']['existing']['install'] = 1
        self.deployment_assertions(expectations)

    def test_compute_scale_out_2_compute(self):
        expectations = self.deploy('scale1')
        expectations['compute']['new']['install'] = 1
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={'node_id': 'compute',
                                              'delta': 2})
        expectations['compute']['new']['install'] = 2
        expectations['compute']['existing']['install'] = 1
        self.deployment_assertions(expectations)

    def test_db_contained_in_compute_scale_out_compute(self):
        expectations = self.deploy('scale2')
        expectations['compute']['new']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={'node_id': 'compute'})
        expectations['compute']['new']['install'] = 1
        expectations['compute']['existing']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        expectations['db']['existing']['install'] = 1
        expectations['db']['existing']['rel_install'] = 2
        self.deployment_assertions(expectations)

    def test_db_contained_in_compute_scale_out_db(self):
        expectations = self.deploy('scale2')
        expectations['compute']['new']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={'node_id': 'db'})
        expectations['compute']['new']['install'] = 1
        expectations['compute']['existing']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        expectations['db']['existing']['install'] = 1
        expectations['db']['existing']['rel_install'] = 2
        self.deployment_assertions(expectations)

    def test_db_contained_in_compute_scale_out_db_operate_on_db(self):
        expectations = self.deploy('scale2')
        expectations['compute']['new']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={
            'node_id': 'db', 'operate_on_compute': False})
        expectations['compute']['existing']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        expectations['db']['existing']['install'] = 1
        expectations['db']['existing']['rel_install'] = 2
        self.deployment_assertions(expectations)

    def test_db_connected_to_compute_scale_out_compute(self):
        expectations = self.deploy('scale3')
        expectations['compute']['new']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={'node_id': 'compute'})
        expectations['compute']['new']['install'] = 1
        expectations['compute']['existing']['install'] = 1
        expectations['db']['existing']['install'] = 1
        expectations['db']['existing']['rel_install'] = 2
        expectations['db']['existing']['scale_rel_install'] = 2
        self.deployment_assertions(expectations)

    def test_db_connected_to_compute_scale_out_db(self):
        expectations = self.deploy('scale3')
        expectations['compute']['new']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        self.deployment_assertions(expectations)

        expectations = self.scale(parameters={'node_id': 'db'})
        expectations['compute']['existing']['install'] = 1
        expectations['db']['new']['install'] = 1
        expectations['db']['new']['rel_install'] = 2
        expectations['db']['existing']['install'] = 1
        expectations['db']['existing']['rel_install'] = 2
        self.deployment_assertions(expectations)

    def setUp(self):
        super(TestScaleWorkflow, self).setUp()
        self.previous_ids = []

    def deployment_assertions(self, expected):
        def expected_invocations(_expectations, num_instances):
            result = {}
            install_count = _expectations.get('install') or 0
            result.update({
                'create': install_count / num_instances,
                'configure': install_count / num_instances,
                'start': install_count / num_instances
            })
            rel_install_count = _expectations.get('rel_install') or 0
            scale_rel_install_count = _expectations.get(
                'scale_rel_install') or 0
            result.update({
                'preconfigure': rel_install_count / num_instances,
                'postconfigure': rel_install_count / num_instances,
                'establish': rel_install_count + scale_rel_install_count /
                num_instances
            })
            return result

        instances = self.client.node_instances.list()

        calculated_expected = {}
        for node_id, expectations in expected.items():
            new_expectation = expectations['new']
            existing_expectation = expectations['existing']
            node_instances = [i for i in instances if i.node_id == node_id]
            new_instances = [i for i in node_instances
                             if i.id not in self.previous_ids]
            existing_instances = [i for i in node_instances
                                  if i.id in self.previous_ids]
            self.assertEqual(len(new_instances),
                             new_expectation.get('install') or 0,
                             'new_instances: {0}, install_expectations: {1}'
                             .format(new_instances,
                                     new_expectation.get('install')))
            self.assertEqual(len(existing_instances),
                             existing_expectation.get('install') or 0,
                             'existing_instances: {0}, '
                             'install_expectations: {1}'
                             .format(existing_instances,
                                     existing_expectation.get('install')))
            for new_instance in new_instances:
                calculated_expected.update({
                    new_instance.id: expected_invocations(
                        new_expectation, len(new_instances))})
            for existing_instance in existing_instances:
                calculated_expected.update({
                    existing_instance.id: expected_invocations(
                        existing_expectation, len(existing_instances))})

        invocations = self.get_plugin_data(
            'testmockoperations', self.deployment_id)[
            'mock_operation_invocation']
        total_expected_count = 0
        for instance_id, operations in calculated_expected.items():
            for operation, expected_count in operations.items():
                total_expected_count += expected_count
                op_invocations = [i for i in invocations
                                  if i['operation'] == operation
                                  and i['id'] == instance_id]
                self.assertEqual(expected_count, len(op_invocations),
                                 'expected_count: {0}, op_invocations: {1}'
                                 .format(expected_count, op_invocations))
        self.assertEqual(total_expected_count, len(invocations))

        # set state for next deployment assertion
        self.previous_ids = [i.id for i in instances]

    def expectations(self):
        return {
            'compute': {
                'new': {},
                'existing': {}
            },
            'db': {
                'new': {},
                'existing': {}
            },
            'webserver': {
                'new': {},
                'existing': {}
            }
        }

    def deploy(self, resource_name):
        deployment, _ = deploy(resource('dsl/{0}.yaml'.format(resource_name)))
        self.deployment_id = deployment.id
        return self.expectations()

    def scale(self, parameters):
        execute_workflow('scale', self.deployment_id, parameters=parameters)
        return self.expectations()
