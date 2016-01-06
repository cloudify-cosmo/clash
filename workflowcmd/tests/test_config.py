########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import yaml

from workflowcmd import config
from workflowcmd import tests


class TestConfig(tests.BaseTest):

    STORAGE_DIR = 'AAA'

    def test_get_storage_dir_plain(self):
        self.user_conf_path.write_text(yaml.safe_dump({
            'storage_dir': self.STORAGE_DIR}))
        self.assertEqual(config.get_storage_dir(
            self._conf(self.user_conf_path)), self.STORAGE_DIR)

    def test_get_storage_dir_env(self):
        self.user_conf_path.write_text(yaml.safe_dump({
            'storage_dir': self.STORAGE_DIR}))
        self.assertEqual(config.get_storage_dir(
            self._conf({'env': 'USER_CONF_PATH'})), self.STORAGE_DIR)

    def test_get_storage_dir_none(self):
        self.assertEqual(config.get_storage_dir(
            self._conf(self.user_conf_path)), None)

    def test_update_storage_dir(self):
        config.update_storage_dir(self._conf(self.user_conf_path),
                                  self.STORAGE_DIR)
        self.assertEqual(self.storage_dir(), self.STORAGE_DIR)

    def _conf(self, path):
        return {'user_config_path': path}
