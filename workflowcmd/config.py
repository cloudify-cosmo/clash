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

WORKFLOWCMD_CONF_PATH = 'WORKFLOWCMD_CONF_PATH'


def workflowcmd_conf_path():
    return os.path.expanduser(os.environ.get(WORKFLOWCMD_CONF_PATH,
                                             '~/.workflowcmd'))


def read_workflowcmd_conf():
    conf_path = workflowcmd_conf_path()
    if not os.path.exists(conf_path):
        return {}
    with open(conf_path) as f:
        return yaml.safe_load(f) or {}


def update_workflowcmd_conf(conf):
    current_conf = read_workflowcmd_conf()
    current_conf.update(conf)
    conf_path = workflowcmd_conf_path()
    with open(conf_path, 'w') as f:
        return yaml.safe_dump(current_conf, f)
