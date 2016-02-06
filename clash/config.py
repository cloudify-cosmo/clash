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

import json

import yaml
from path import path

from clash import functions


class Config(object):

    def __init__(self, config_path):
        config_path = path(config_path).expanduser().abspath()
        self.config = json.loads(json.dumps(yaml.safe_load(
            config_path.text())))
        self.config_dir = config_path.dirname()

    @property
    def name(self):
        return self.config['name']

    @property
    def user_config_path(self):
        result = self.config['user_config_path']
        if isinstance(result, dict):
            result = functions.parse_parameters(
                parameters={'holder': result},
                loader=None,
                args=None)['holder']
        return path(result).expanduser()

    @property
    def user_config(self):
        return UserConfig(self.user_config_path)

    @property
    def blueprint_path(self):
        return (self.config_dir / self.config['blueprint_path']).abspath()

    @property
    def blueprint_dir(self):
        return self.blueprint_path.dirname()

    @property
    def env_create(self):
        return self.config.get('env_create', {})

    @property
    def commands(self):
        return self.config.get('commands', {})

    @property
    def task(self):
        return self.config.get('task', {})

    @property
    def event_cls(self):
        return self.config.get('event_cls')

    @property
    def hooks(self):
        return ConfigHooks(self.config.get('hooks', {}))

    @property
    def ignored_modules(self):
        return self.config.get('ignored_modules', [])

    @property
    def command_after_init_on_apply(self):
        return self.config.get('command_after_init_on_apply')


class ConfigHooks(object):

    def __init__(self, hooks):
        self.hooks = hooks

    @property
    def after_env_create(self):
        return self.hooks.get('after_env_create')

    @property
    def before_init(self):
        return self.hooks.get('before_init')


class UserConfig(object):

    def __init__(self, user_config_path):
        self.user_config_path = user_config_path
        self._user_config = None

    @property
    def user_config(self):
        if self._user_config:
            return self._user_config
        if not self.user_config_path.exists():
            return {}
        result = yaml.safe_load(self.user_config_path.text())
        self._user_config = result
        return result

    @user_config.setter
    def user_config(self, value):
        self._user_config = value
        self.user_config_path.write_text(yaml.safe_dump(value))

    @property
    def configurations(self):
        return self.user_config.get('configurations', {})

    @configurations.setter
    def configurations(self, value):
        user_config = self.user_config
        user_config['configurations'] = value
        self.user_config = user_config

    @property
    def configuration_names(self):
        return self.configurations.keys()

    def remove_configuration(self, name):
        configurations = self.configurations
        configurations.pop(name, None)
        self.configurations = configurations
        if self.current == name:
            self.current = next(iter(self.configuration_names), None)

    @property
    def current(self):
        return self.user_config.get('current', '')

    @current.setter
    def current(self, value):
        user_config = self.user_config
        user_config['current'] = value
        self.user_config = user_config

    @property
    def current_user_config(self):
        return self.configurations.get(self.current, {})

    @current_user_config.setter
    def current_user_config(self, value):
        configurations = self.configurations
        configurations[self.current] = value
        self.configurations = configurations

    @property
    def storage_dir(self):
        current_user_config = self.current_user_config
        storage_dir = current_user_config.get('storage_dir')
        if not storage_dir:
            return None
        return path(storage_dir)

    @storage_dir.setter
    def storage_dir(self, value):
        current_user_config = self.current_user_config
        current_user_config['storage_dir'] = str(value)
        self.current_user_config = current_user_config

    @property
    def editable(self):
        return self.current_user_config.get('editable', False)

    @editable.setter
    def editable(self, value):
        current_user_config = self.current_user_config
        current_user_config['editable'] = value
        self.current_user_config = current_user_config

    @property
    def inputs_path(self):
        storage_dir = self.storage_dir
        if not storage_dir:
            return None
        return storage_dir / 'inputs.yaml'

    @property
    def inputs(self):
        inputs_path = self.inputs_path
        if not inputs_path or not inputs_path.exists():
            return {}
        return yaml.safe_load(inputs_path.text()) or {}

    @inputs.setter
    def inputs(self, value):
        self.inputs_path.write_text(
                yaml.safe_dump(value, default_flow_style=False))

    @property
    def macros_path(self):
        storage_dir = self.storage_dir
        if not storage_dir:
            return None
        return storage_dir / 'macros.yaml'

    @property
    def macros(self):
        macros_path = self.macros_path
        if not macros_path or not macros_path.exists():
            return {}
        return yaml.safe_load(macros_path.text()) or {}
