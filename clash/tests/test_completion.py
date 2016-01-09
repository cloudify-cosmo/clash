#! /usr/bin/env python
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

import sh

import clash
from clash import tests
from clash.tests import resources


CONFIG_PATH = 'completions.yaml'


class TestCompletion(tests.BaseTest):

    help_args = ['-h', '--help']

    def test_basic(self):
        self.assert_completion(expected=['setup'] + self.help_args)

    def test_setup(self):
        base_setup_options = ['-r', '--reset',
                              '-s', '--storage-dir']
        user_setup_options = ['--arg2']
        arg1_completer_options = setup_arg1_completer()
        expected = (base_setup_options + user_setup_options +
                    self.help_args + arg1_completer_options)
        self.assert_completion(expected=expected,
                               args=['setup'],
                               filter_non_options=False)
        self.assert_completion(expected=setup_arg2_completer(),
                               args=['setup', 'arg1_value', '--arg2'],
                               filter_non_options=False)

    def test_init(self):
        self.dispatch(CONFIG_PATH, 'setup', 'arg')
        self.assert_completion(expected=['-r', '--reset'] + self.help_args,
                               args=['init'])

    def test_outputs(self):
        self.dispatch(CONFIG_PATH, 'setup', 'arg')
        self.assert_completion(expected=['-j', '--json'] + self.help_args,
                               args=['outputs'])

    def test_user_command(self):
        base_options = ['-v', '--verbose'] + self.help_args
        user_options = ['--arg2']
        self.dispatch(CONFIG_PATH, 'setup', 'arg')
        self.dispatch(CONFIG_PATH, 'init')
        completer_options = ['.local', '1']
        expected = base_options + user_options + completer_options
        self.assert_completion(expected=expected,
                               args=['command1'])
        completer_options = ['.local', '2']
        self.assert_completion(expected=completer_options,
                               args=['command1', 'arg', '--arg2'])

    def assert_completion(self, expected, args=None,
                          filter_non_options=False):

        project_dir = os.path.dirname(os.path.dirname(clash.__file__))
        this_file = os.path.basename(__file__)
        if this_file.endswith('.pyc'):
            this_file = this_file[:-1]
        this_dir = os.path.dirname(__file__)

        args = args or []
        args += ["''"]
        cmd = [this_file] + list(args)
        partial_word = cmd[-1]
        cmdline = ' '.join(cmd)
        lines = [
            'set -e',
            'export PATH={}:$PATH'.format(this_dir),
            'export PYTHONPATH={}:$PYTHONPATH'.format(project_dir),
            'eval "$(register-python-argcomplete {})"'.format(this_file),
            'export COMP_LINE="{}"'.format(cmdline),
            'export COMP_WORDS=({})'.format(cmdline),
            'export COMP_CWORD={}'.format(cmd.index(partial_word)),
            'export COMP_POINT={}'.format(len(cmdline)),
            '_python_argcomplete {}'.format(this_file),
            'echo ${COMPREPLY[*]}'
        ]
        script_path = self.workdir / 'completions.sh'
        script_path.write_text('\n'.join(lines))
        try:
            p = sh.bash(script_path)
        except sh.ErrorReturnCode as e:
            self.fail('out: {}, err: {}'.format(e.stdout, e.stderr))
        completions = p.stdout.strip().split(' ')
        if filter_non_options:
            completions = [c for c in completions if c.startswith('-')]
        self.assertEqual(len(expected), len(completions),
                         'expected: {}, actual: {}'.format(expected,
                                                           completions))
        for expected_completion in expected:
            self.assertIn(expected_completion, completions)


def setup_arg1_completer(*arg, **kwarg):
    return ['one', 'two', 'three']


def setup_arg2_completer(*arg, **kwargs):
    return ['four', 'five', 'six']


def user_arg1_completer(env, *arg, **kwarg):
    return [env.name, '1']


def user_arg2_completer(env, *arg, **kwargs):
    return [env.name, '2']


def main():
    config_path = '{0}/configs/{1}'.format(os.path.dirname(resources.__file__),
                                           CONFIG_PATH)
    clash.dispatch(config_path)

if __name__ == '__main__':
    main()
