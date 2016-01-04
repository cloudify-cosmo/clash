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

import tempfile
import unittest
import shutil
import os
import sys

import sh
import yaml
from path import path

from workflowcmd import dispatch
from workflowcmd import config
from workflowcmd.tests import resources


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='workflowcmd-tests-'))
        self.workflowcmd_conf_path = self.workdir / '.conf'
        os.environ[config.WORKFLOWCMD_CONF_PATH] = self.workflowcmd_conf_path
        self.addCleanup(self.cleanup)

    def cleanup(self):
        shutil.rmtree(self.workdir, ignore_errors=True)
        os.environ.pop(config.WORKFLOWCMD_CONF_PATH, None)

    def dispatch(self, config_path, *args, **kwargs):
        with self.workdir:
            try:
                command = sh.Command(sys.executable).bake(__file__)
                command(config_path, *args, **kwargs)
            except sh.ErrorReturnCode as e:
                print 'out: {0}\nerr: {1}\n'.format(e.stdout, e.stderr)
                raise

    def config(self, config_path):
        with open(resources.DIR / 'configs' / config_path) as f:
            return yaml.safe_load(f)

    def workflowcmd_conf(self):
        with open(self.workflowcmd_conf_path) as f:
            return yaml.safe_load(f)

    def storage_dir(self, config_path):
        conf = self.config(config_path)
        return path(self.workflowcmd_conf()[conf['name']]['storage_dir'])

    def inputs(self, config_path):
        storage_dir = self.storage_dir(config_path)
        return yaml.safe_load((storage_dir / 'inputs.yaml').text())


def main():
    config_path = sys.argv[1]
    config_path = 'configs/{0}'.format(config_path)
    sys.argv.pop(1)
    dispatch(resources, config_path)


if __name__ == '__main__':
    main()
