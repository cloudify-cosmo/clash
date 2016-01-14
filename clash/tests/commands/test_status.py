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

from clash import tests


class TestStatus(tests.BaseTest):

    def test_basic(self):
        output = self._test(json=False)
        self.assertIn('output: output_value', output)
        self.assertIn('current: main', output)

    def test_json(self):
        actual = _json.loads(self._test(json=True))
        expected = {
            'env': {
                'current': 'main',
                'storage_dir': str(self.storage_dir()),
                'editable': self.editable()
            },
            'outputs': {'output': 'output_value'}
        }
        self.assertEqual(expected, actual)

    def _test(self, json):
        config_path = 'outputs.yaml'
        self.dispatch(config_path, 'env', 'create')
        self.dispatch(config_path, 'init')
        return self.dispatch(config_path, 'status', json=json).stdout
