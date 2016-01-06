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
from path import path

from workflowcmd import functions


def _get_user_config_path(config):
    user_config_path = config['user_config_path']
    if isinstance(user_config_path, dict):
        user_config_path = functions.parse_parameters(
            parameters={'holder': user_config_path},
            loader=None,
            args=None)['holder']
    user_config_path = path(user_config_path).expanduser()
    return user_config_path


def get_storage_dir(config):
    user_config_path = _get_user_config_path(config)
    if not user_config_path.exists():
        return None
    user_config = yaml.safe_load(user_config_path.text())
    return path(user_config['storage_dir'])


def update_storage_dir(config, storage_dir):
    user_config_path = _get_user_config_path(config)
    user_config_path.write_text(yaml.safe_dump({
        'storage_dir': storage_dir
    }))
