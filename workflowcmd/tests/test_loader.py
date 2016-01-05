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

from workflowcmd import loader
from workflowcmd import tests
from workflowcmd.tests import resources


class TestLoader(tests.BaseTest):

    relative_config_path = path('configs') / 'plain.yaml'
    full_config_path = resources.DIR / relative_config_path

    def test_properties(self):
        loader = self._init_loader()
        config1 = yaml.safe_load(self.full_config_path.text())
        expected_blueprint_path = (self.full_config_path.dirname() /
                                   config1['blueprint_path'])
        expected_blueprint_dir = expected_blueprint_path.dirname()
        self.assertEqual(loader.config, config1)
        self.assertEqual(loader.blueprint_path, expected_blueprint_path)
        self.assertEqual(loader.blueprint_dir, expected_blueprint_dir)
        self.assertIsNone(loader.storage_dir)

    def _init_loader(self):
        return loader.Loader(package=resources,
                             config_path=self.relative_config_path)
