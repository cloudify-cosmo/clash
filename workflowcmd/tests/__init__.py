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

from cloudify.workflows import local

import workflowcmd
from workflowcmd import dispatch
from workflowcmd.tests import resources


USER_CONF_PATH = 'USER_CONF_PATH'


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='workflowcmd-tests-'))
        self.user_conf_path = self.workdir / 'user_conf'
        os.environ[USER_CONF_PATH] = self.user_conf_path
        self.addCleanup(self.cleanup)

    def cleanup(self):
        shutil.rmtree(self.workdir, ignore_errors=True)
        os.environ.pop(USER_CONF_PATH, None)

    def dispatch(self, config_path, *args, **kwargs):
        # for tox
        python_path = '{0}{1}{2}'.format(
            path(workflowcmd.__file__).dirname().dirname(),
            os.pathsep,
            os.environ.get('PYTHONPATH', '.'))
        env = os.environ.copy()
        env['PYTHONPATH'] = python_path
        with self.workdir:
            try:
                command = sh.Command(sys.executable).bake(__file__, _env=env)
                return command(config_path, *args, **kwargs)
            except sh.ErrorReturnCode as e:
                print 'out: {0}\nerr: {1}\n'.format(e.stdout, e.stderr)
                raise

    def config(self, config_path):
        with open(resources.DIR / 'configs' / config_path) as f:
            return yaml.safe_load(f)

    def user_conf(self):
        with open(self.user_conf_path) as f:
            return yaml.safe_load(f)

    def storage_dir(self):
        return path(self.user_conf()['storage_dir'])

    def inputs(self):
        storage_dir = self.storage_dir()
        return yaml.safe_load((storage_dir / 'inputs.yaml').text())

    def set_inputs(self, inputs):
        storage_dir = self.storage_dir()
        (storage_dir / 'inputs.yaml').write_text(yaml.safe_dump(inputs))

    def env(self):
        storage_dir = self.storage_dir()
        storage = local.FileStorage(storage_dir)
        return local.load_env('.local', storage)


def main():
    config_path = sys.argv[1]
    config_path = '{0}/configs/{1}'.format(os.path.dirname(resources.__file__),
                                           config_path)
    sys.argv.pop(1)
    dispatch(config_path)


if __name__ == '__main__':
    main()
