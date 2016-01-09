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

from contextlib import contextmanager

import yaml
from path import path

from clash import functions


def _get_user_config_path(config):
    user_config_path = config['user_config_path']
    if isinstance(user_config_path, dict):
        user_config_path = functions.parse_parameters(
            parameters={'holder': user_config_path},
            loader=None,
            args=None)['holder']
    user_config_path = path(user_config_path).expanduser()
    return user_config_path


def _load_user_config(config):
    user_config_path = _get_user_config_path(config)
    if not user_config_path.exists():
        return {}
    return yaml.safe_load(user_config_path.text())


def _update_user_config(config, user_config):
    user_config_path = _get_user_config_path(config)
    user_config_path.write_text(yaml.safe_dump(user_config))


@contextmanager
def _user_config(config):
    user_config = _load_user_config(config)
    yield user_config
    _update_user_config(config, user_config)


def get_storage_dir(config):
    user_config = _load_user_config(config)
    storage_dir = user_config.get('storage_dir')
    if not storage_dir:
        return None
    return path(storage_dir)


def update_storage_dir(config, storage_dir):
    with _user_config(config) as user_config:
        user_config.update({
            'storage_dir': storage_dir
        })


def is_editable(config):
    user_config = _load_user_config(config)
    return user_config.get('editable', False)


def update_editable(config, editable):
    with _user_config(config) as user_config:
        user_config.update({
            'editable': editable
        })
