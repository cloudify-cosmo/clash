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

import os

import yaml
from path import path
from mock import patch

from clash import config
from clash import tests


class TestConfig(tests.BaseTest):

    def setUp(self):
        super(TestConfig, self).setUp()
        self.config_path = self.workdir / 'config.yaml'

    def test_config_dir(self):
        self._save({})
        self.assertEqual(self.conf.config_dir, self.workdir)

    def test_name(self):
        self._save({'name': 'HELLO'})
        self.assertEqual(self.conf.name, 'HELLO')

    def test_user_config_path(self):
        self._save({'user_config_path': '~/hello'})
        self.assertEqual(self.conf.user_config_path,
                         path('~/hello').expanduser())
        self._save({'user_config_path': {'env': 'HELLO'}})
        with patch.dict(os.environ, {'HELLO': 'WORLD'}):
            self.assertEqual(self.conf.user_config_path, 'WORLD')

    def test_user_config(self):
        self._save({'user_config_path': str(self.user_conf_path)})
        self.user_conf_path.write_text(yaml.safe_dump({'current': 'now'}))
        self.assertEqual(self.conf.user_config.current, 'now')

    def test_blueprint_path_and_dir(self):
        self._save({'blueprint_path': '../hello.yaml'})
        self.assertEqual(self.conf.blueprint_path,
                         self.workdir.dirname() / 'hello.yaml')
        self.assertEqual(self.conf.blueprint_dir, self.workdir.dirname())

    def test_env_create(self):
        self._save({})
        self.assertEqual(self.conf.env_create, {})
        self._save({'env_create': {'hello': 'world'}})
        self.assertEqual(self.conf.env_create, {'hello': 'world'})

    def test_commands(self):
        self._save({})
        self.assertEqual(self.conf.commands, {})
        self._save({'commands': {'hello': 'world'}})
        self.assertEqual(self.conf.commands, {'hello': 'world'})

    def test_task(self):
        self._save({})
        self.assertEqual(self.conf.task, {})
        self._save({'task': {'hello': 'world'}})
        self.assertEqual(self.conf.task, {'hello': 'world'})

    def test_event_cls(self):
        self._save({})
        self.assertIsNone(self.conf.event_cls)
        self._save({'event_cls': 'my_class'})
        self.assertEqual(self.conf.event_cls, 'my_class')

    def test_hooks(self):
        self._save({})
        hooks = self.conf.hooks
        self.assertIsNone(hooks.after_env_create)
        self.assertIsNone(hooks.before_init)
        self._save({'hooks': {'after_env_create': 'ONE',
                              'before_init': 'TWO'}})
        hooks = self.conf.hooks
        self.assertEqual(hooks.after_env_create, 'ONE')
        self.assertEqual(hooks.before_init, 'TWO')

    def test_ignored_modules(self):
        self._save({})
        self.assertEqual(self.conf.ignored_modules, [])
        self._save({'ignored_modules': ['one', 'two']})
        self.assertEqual(self.conf.ignored_modules, ['one', 'two'])

    def test_command_after_init_on_apply(self):
        self._save({})
        self.assertIsNone(self.conf.command_after_init_on_apply)
        self._save({'command_after_init_on_apply': 'my_command'})
        self.assertEqual(self.conf.command_after_init_on_apply, 'my_command')

    def _save(self, value):
        self.config_path.write_text(yaml.safe_dump(value))

    @property
    def conf(self):
        return config.Config(self.config_path)


class TestUserConfig(tests.BaseTest):

    def setUp(self):
        super(TestUserConfig, self).setUp()
        self._reload()

    def _reload(self):
        self.user_config = config.UserConfig(self.user_conf_path)

    def test_user_config_no_file(self):
        self.assertEquals(self.user_config.user_config, {})

    def test_user_config(self):
        user_config = {'hello': 'world'}
        # test setter
        self.user_config.user_config = user_config
        self.assertEqual(self.user_conf(), user_config)
        self._reload()
        # test getter
        self.assertEqual(self.user_config.user_config, user_config)

    def test_configurations(self):
        configurations = {'hello': 'world'}
        self.user_config.configurations = configurations
        self.assertEqual(self.user_config.configurations, configurations)
        self._reload()
        self.assertEqual(self.user_config.configurations, configurations)
        self.assertEqual(self.user_config.configuration_names, ['hello'])

    def test_remove_configuration(self):
        user_config = {'configurations': {'hello': 'world',
                                          'goodbye': 'night'},
                       'current': 'hello'}
        self.user_config.user_config = user_config
        self.assertEqual(self.user_config.current, 'hello')
        self.user_config.remove_configuration('hello')
        self._reload()
        self.assertEqual(self.user_config.current, 'goodbye')
        self.assertEqual(self.user_config.configurations, {'goodbye': 'night'})
        self.user_config.remove_configuration('goodbye')
        self._reload()
        self.assertIsNone(self.user_config.current)

    def test_current(self):
        user_config = {'current': 'one'}
        self.user_config.user_config = user_config
        self._reload()
        self.assertEqual(self.user_config.current, 'one')
        self.user_config.current = 'two'
        self._reload()
        self.assertEqual(self.user_config.current, 'two')

    def test_current_user_config(self):
        user_config = {'configurations': {'hello': {'world': 'war'}},
                       'current': 'hello'}
        self.user_config.user_config = user_config
        self.user_config.current_user_config = {'world2': 'war2'}
        self._reload()
        self.assertEqual(self.user_config.current_user_config,
                         {'world2': 'war2'})

    def test_storage_dir(self):
        self.assertIsNone(self.user_config.storage_dir)
        user_config = {
            'current': 'main',
            'configurations': {
                'main': {'storage_dir': 'AAA'}
            }
        }
        self.user_config.user_config = user_config
        self._reload()
        self.assertEqual(self.user_config.storage_dir, 'AAA')

    def test_editable(self):
        self.assertIs(self.user_config.editable, False)
        self.user_config.user_config = {
            'current': 'main',
            'configurations': {
                'main': {'editable': True}
            }
        }
        self._reload()
        self.assertIs(self.user_config.editable, True)
