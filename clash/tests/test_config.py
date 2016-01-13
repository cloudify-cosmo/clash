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

from clash import config
from clash import tests


class TestConfig(tests.BaseTest):

    STORAGE_DIR = 'AAA'

    def test_get_storage_dir_plain(self):
        self.user_conf_path.write_text(yaml.safe_dump(self._user_conf(
            'main', {'storage_dir': self.STORAGE_DIR})))
        self.assertEqual(config.get_storage_dir(
            self._conf(self.user_conf_path)), self.STORAGE_DIR)

    def test_get_storage_dir_env(self):
        self.user_conf_path.write_text(yaml.safe_dump(self._user_conf(
            'main', {'storage_dir': self.STORAGE_DIR})))
        self.assertEqual(config.get_storage_dir(
            self._conf({'env': 'USER_CONF_PATH'})), self.STORAGE_DIR)

    def test_get_storage_dir_none(self):
        self.assertEqual(config.get_storage_dir(
            self._conf(self.user_conf_path)), None)

    def test_update_storage_dir(self):
        storage_dir2 = 'BBB'
        conf = self._conf(self.user_conf_path)
        config.set_current(conf, 'main')
        config.update_storage_dir(conf, self.STORAGE_DIR)
        self.assertEqual(self.storage_dir('main'), self.STORAGE_DIR)
        config.set_current(conf, 'second')
        config.update_storage_dir(conf, storage_dir2)
        self.assertEqual(self.storage_dir('main'), self.STORAGE_DIR)
        self.assertEqual(self.storage_dir('second'), storage_dir2)

    def test_is_editable(self):
        self.user_conf_path.write_text(yaml.safe_dump(self._user_conf(
                'main', {'editable': True})))
        self.assertTrue(config.is_editable(self._conf(self.user_conf_path)))

    def test_is_editable_default(self):
        self.assertFalse(config.is_editable(self._conf(self.user_conf_path)))

    def test_update_editable(self):
        conf = self._conf(self.user_conf_path)
        config.set_current(conf, 'main')
        config.update_editable(conf, True)
        self.assertTrue(self.editable('main'))
        config.set_current(conf, 'second')
        config.update_editable(conf, False)
        self.assertTrue(self.editable('main'))
        self.assertFalse(self.editable('second'))
        config.update_editable(conf, True)
        self.assertTrue(self.editable('second'))

    def test_configurations(self):
        configurations = {
            'main': {'editable': True},
            'second': {'editable': False}
        }
        self.user_conf_path.write_text(yaml.safe_dump({
            'current': 'main',
            'configurations': configurations}))
        self.assertEqual(configurations, config.configurations(
            self._conf(self.user_conf_path)))
        self.assertEqual(
            set(configurations.keys()),
            set(config.configuration_names(self._conf(self.user_conf_path))))
        return configurations

    def test_remove_configuration(self):
        configurations = self.test_configurations()
        name = 'second'
        configurations.pop(name)
        config.remove_configuration(self._conf(self.user_conf_path), name)
        self.assertEqual(
            configurations,
            config.configurations(self._conf(self.user_conf_path)))

    def test_get_current(self):
        self.user_conf_path.write_text(yaml.safe_dump(self._user_conf(
                'main', {})))
        self.assertEqual('main', config.get_current(
            self._conf(self.user_conf_path)))

    def test_set_current(self):
        config.set_current(self._conf(self.user_conf_path), 'second')
        self.assertEqual(self.current(), 'second')

    def _conf(self, path):
        return {'user_config_path': path}

    def _user_conf(self, name, current):
        return {
            'current': name,
            'configurations': {
                name: current
            }
        }
