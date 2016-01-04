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

from path import path

from workflowcmd import config


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='workflowcmd-tests-'))
        self.workflowcmd_conf_path = self.workdir / '.conf'
        os.environ[config.WORKFLOWCMD_CONF_PATH] = self.workflowcmd_conf_path

    def cleanup(self):
        shutil.rmtree(self.workdir, ignore_errors=True)
        del os.environ[config.WORKFLOWCMD_CONF_PATH]
