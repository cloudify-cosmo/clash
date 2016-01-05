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

import json as _json

from workflowcmd import tests


class TestOutputs(tests.BaseTest):

    def test_basic(self):
        self.assertIn('output: output_value', self._test(json=False))

    def test_json(self):
        self.assertEqual({'output': 'output_value'},
                         _json.loads(self._test(json=True)))

    def _test(self, json):
        config_path = 'outputs.yaml'
        self.dispatch(config_path, 'setup')
        self.dispatch(config_path, 'init')
        return self.dispatch(config_path, 'outputs', json=json).stdout
