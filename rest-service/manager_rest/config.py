#########
# Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
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


class Config(object):

    def __init__(self):
        self.db_address = 'localhost'
        self.db_port = 9200
        self.amqp_address = 'localhost'
        self.amqp_username = 'testuser'
        self.amqp_password = 'testpass'
        self.file_server_root = None
        self.file_server_base_uri = None
        self.file_server_blueprints_folder = None
        self.file_server_uploaded_blueprints_folder = None
        self.file_server_resources_uri = None
        self.rest_service_log_level = None
        self.rest_service_log_path = None
        self.rest_service_log_file_size_MB = None
        self.rest_service_log_files_backup_count = None
        self.test_mode = False
        self.secured_server = False
        self.auth_token_generator = None
        self.security_bypass_port = None
        self.securest_log_level = None
        self.securest_log_file = None
        self.securest_log_file_size_MB = None
        self.securest_log_files_backup_count = None
        self.securest_userstore_driver = None
        self.securest_authentication_providers = []

_instance = Config()


def reset(configuration=None):
    global _instance
    if configuration is not None:
        _instance = configuration
    else:
        _instance = Config()


def instance():
    return _instance
