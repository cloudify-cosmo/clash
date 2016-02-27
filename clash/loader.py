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

import argparse
import sys
import os
import shutil
import tempfile
import json as _json
import StringIO
import copy

import yaml
import argh
from path import path

from cloudify.workflows import local

from clash import output
from clash import functions
from clash import module
from clash import config
from clash import state


class Loader(object):

    _name = '.local'

    def __init__(self, config_path):
        self.config = config.Config(config_path)
        self.user_config = self.config.user_config
        self.user_commands = {}
        self._parser = argh.ArghParser()
        env_commands = [self._parse_env_create_command()]
        if self.user_config.storage_dir:
            env_commands += self._parse_env_subcommands()
            self._parse_commands(commands=self.config.commands,
                                 macros=self.user_config.macros)
            self._parser.add_commands(functions=[self._init_command,
                                                 self._status_command,
                                                 self._apply_command])
        self._parser.add_commands(functions=env_commands, namespace='env')

    def _parse_commands(self, commands, macros, namespace=None):
        functions = []
        for name, command in commands.items():
            if 'workflow' not in command and 'function' not in command:
                self._parse_commands(commands=command, namespace=name,
                                     macros=macros.get(name, {}))
                continue
            functions.append(self._parse_command(name=name, command=command))
        for function in functions:
            name = function.argh_name
            if namespace:
                name = '{}.{}'.format(namespace, name)
            self.user_commands[name] = function
        for name, macro in macros.items():
            if 'commands' not in macro:
                if name in commands:
                    # namespace already handled by existing commands namespace
                    continue
                self._parse_commands(commands={}, namespace=name,
                                     macros=macro)
                continue
            functions.append(self._parse_macro(name=name, macro=macro))
        self._parser.add_commands(functions=functions, namespace=namespace)

    def _parse_command(self, name, command):
        if 'function' in command:
            @argh.expects_obj
            @argh.named(name)
            def func(args):
                self._set_paths()
                function = module.load_attribute(command['function'])
                kwargs = vars(args)
                kwargs.pop('_functions_stack', None)
                state.current_loader.set(self)
                try:
                    return function(**kwargs)
                finally:
                    state.current_loader.clear()
        else:
            @argh.expects_obj
            @argh.named(name)
            @argh.arg('-v', '--verbose', default=False)
            def func(args):
                self._set_paths()
                parameters = functions.parse_parameters(
                    loader=self,
                    parameters=copy.deepcopy(command.get('parameters', {})),
                    args=vars(args))
                task_config = {
                    'retries': 0,
                    'retry_interval': 1,
                    'thread_pool_size': 1
                }
                global_task_config = self.config.task
                command_task_config = command.get('task', {})
                task_config.update(global_task_config)
                task_config.update(command_task_config)
                env = self.env

                event_cls = command.get('event_cls',
                                        self.config.event_cls)
                output.setup_output(event_cls=event_cls,
                                    verbose=args.verbose,
                                    env=env,
                                    command=command)

                return env.execute(
                    workflow=command['workflow'],
                    parameters=parameters,
                    task_retries=task_config['retries'],
                    task_retry_interval=task_config['retry_interval'],
                    task_thread_pool_size=task_config['thread_pool_size'])
        self._add_args_to_func(func, command.get('args', []), skip_env=False)
        return func

    def _parse_macro(self, name, macro):
        @argh.expects_obj
        @argh.named(name)
        def func(args):
            self._set_paths()
            args = vars(args)
            for user_command in macro['commands']:
                user_command_name = user_command['name']
                user_command_args = functions.parse_parameters(
                    loader=self,
                    parameters=user_command.get('args', []),
                    args=args)
                print '==> {0}: {1}'.format(user_command_name,
                                            user_command_args)
                user_command_func = self.user_commands[user_command_name]
                argh.dispatch_command(user_command_func,
                                      argv=user_command_args)
        self._add_args_to_func(func, macro.get('args', []), skip_env=False)
        return func

    @property
    def env(self):
        return self._load_env()

    def _load_env(self):
        return local.load_env(name=self._name, storage=self._storage())

    def _storage(self):
        return local.FileStorage(storage_dir=self.user_config.storage_dir)

    def _parse_env_create_command(self):
        env_create = self.config.env_create

        @argh.expects_obj
        @argh.named('create')
        def func(args):
            if (self.user_config.current == args.name and
                    self.user_config.storage_dir and not args.reset):
                raise argh.CommandError('storage dir already configured. pass '
                                        '--reset to override.')
            storage_dir = args.storage_dir or os.getcwd()
            self.user_config.current = args.name
            self.user_config.editable = args.editable
            self.user_config.storage_dir = storage_dir
            self.user_config.storage_dir.mkdir_p()
            self._create_inputs(args, env_create.get('inputs', {}))
            self.user_config.macros_path.touch()
            after_env_create_func = self.config.hooks.after_env_create
            if after_env_create_func:
                after_env_create = module.load_attribute(after_env_create_func)
                after_env_create(self, **vars(args))
        self._add_args_to_func(func, env_create.get('args', []), skip_env=True)
        argh.arg('-s', '--storage-dir')(func)
        argh.arg('-r', '--reset', default=False)(func)
        argh.arg('-e', '--editable', default=False)(func)
        argh.arg('-n', '--name', default='main')(func)
        return func

    def _set_paths(self):
        # PATH
        bin_dir = path(sys.executable).dirname()
        current_path_env = os.environ.get('PATH', '')
        if bin_dir not in current_path_env:
            os.environ['PATH'] = '{}{}{}'.format(bin_dir,
                                                 os.pathsep,
                                                 current_path_env)
        # PYTHONPATH
        resources = self.user_config.storage_dir / self._name / 'resources'
        for python_path in [self.user_config.storage_dir, resources]:
            if python_path not in sys.path:
                sys.path.append(python_path)

    def _create_inputs(self, args, env_create_inputs):
        inputs = {}

        with open(self.config.blueprint_path) as f:
            blueprint = yaml.safe_load(f) or {}
        blueprint_inputs = blueprint.get('inputs', {})
        blueprint_inputs_defaults = {
            key: value.get('default', '_')
            for key, value in blueprint_inputs.items()}

        env_create_inputs = functions.parse_parameters(
            loader=self,
            parameters=env_create_inputs,
            args=vars(args))

        inputs.update(blueprint_inputs_defaults)
        inputs.update(env_create_inputs)

        self.user_config.inputs = inputs

        inputs_lines = self.user_config.inputs_path.lines()
        new_input_lines = []

        first_line = True

        blueprint_description = blueprint.get('description', '').strip()
        if blueprint_description:
            blueprint_description = blueprint_description.replace('\n',
                                                                  '\n# ')
            new_input_lines.append('# {}\n'.format(blueprint_description))
            new_input_lines.append('\n')
            first_line = False

        for line in inputs_lines:
            possible_key = line.split(':')[0]
            if possible_key in inputs:
                if not first_line:
                    new_input_lines.append('\n')
                key = possible_key
                description = blueprint_inputs.get(key, {}).get(
                    'description', '').strip()
                if description:
                    description = description.replace('\n', '\n# ')
                    new_input_lines.append('# {}'.format(description))
            new_input_lines.append(line)
            first_line = False

        self.user_config.inputs_path.write_lines(new_input_lines)

    @argh.named('init')
    def _init_command(self, reset=False):
        local_dir = self.user_config.storage_dir / self._name
        if local_dir.exists():
            if reset:
                shutil.rmtree(local_dir)
            else:
                raise argh.CommandError('Already initialized, pass --reset '
                                        'to re-initialize.')
        inputs = self.user_config.inputs
        temp_dir = path(tempfile.mkdtemp(
            prefix='{}-blueprint-dir-'.format(self.config.name)))
        blueprint_dir = temp_dir / 'blueprint'
        try:
            shutil.copytree(self.config.blueprint_dir, blueprint_dir)
            sys.path.append(blueprint_dir)
            blueprint_path = (blueprint_dir /
                              self.config.blueprint_path.basename())
            before_init_func = self.config.hooks.before_init
            if before_init_func:
                blueprint = yaml.safe_load(blueprint_path.text())
                before_init = module.load_attribute(before_init_func)
                before_init(blueprint=blueprint,
                            inputs=inputs,
                            loader=self)
                blueprint_path.write_text(yaml.safe_dump(blueprint))
            local.init_env(blueprint_path=blueprint_path,
                           inputs=inputs,
                           name=self._name,
                           storage=self._storage(),
                           ignored_modules=self.config.ignored_modules)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        if self.user_config.editable:
            resources_path = (self.user_config.storage_dir / self._name /
                              'resources')
            shutil.rmtree(resources_path, ignore_errors=True)
            os.symlink(self.config.blueprint_dir, resources_path)

    def _parse_env_subcommands(self):
        configuration_names = self.user_config.configuration_names

        def name_completer(prefix, *args, **kwargs):
            return (n for n in configuration_names if n.startswith(prefix))

        @argh.named('use')
        def _use_command(name):
            if name not in configuration_names:
                raise argh.CommandError('No such configuration: {}'
                                        .format(name))
            self.user_config.current = name
        argh.arg('name', completer=name_completer)(_use_command)

        @argh.named('remove')
        def _remove_command(name):
            if name not in configuration_names:
                raise argh.CommandError('No such configuration: {}')
            self.user_config.remove_configuration(name)
        argh.arg('name', completer=name_completer)(_remove_command)

        @argh.named('list')
        def _list_command():
            return '\n'.join(configuration_names)

        return [_use_command, _remove_command, _list_command]

    @argh.named('status')
    def _status_command(self, json=False):
        try:
            outputs = self.env.outputs()
        except Exception as e:
            outputs = {'error': str(e)}
        status = {
            'env': {
                'current': self.user_config.current,
                'storage_dir': str(self.user_config.storage_dir),
                'editable': self.user_config.editable
            },
            'outputs': outputs
        }
        if json:
            return _json.dumps(status, sort_keys=True, indent=2)
        else:
            return yaml.safe_dump(status, default_flow_style=False)

    @argh.named('apply')
    def _apply_command(self, verbose=False):
        self._init_command(reset=True)
        user_command = self.config.command_after_init_on_apply
        if user_command:
            user_command_func = self.user_commands[user_command]
            user_command_func(argparse.Namespace(verbose=verbose))

    def _add_args_to_func(self, func, args, skip_env):
        for arg in reversed(args):
            name = arg.pop('name')
            completer = arg.pop('completer', None)
            if completer:
                completer = module.load_attribute(completer)
                completer = Completer(None if skip_env else self._load_env,
                                      completer)
                arg['completer'] = completer
            name = name if isinstance(name, list) else [name]
            argh.arg(*name, **arg)(func)

    def dispatch(self):
        errors = StringIO.StringIO()
        self._parser.dispatch(errors_file=errors)
        errors_value = errors.getvalue()
        if errors_value:
            errors_value = errors_value.replace('CommandError',
                                                'error').strip()
            sys.exit(errors_value)


def dispatch(config_path):
    loader = Loader(config_path=config_path)
    loader.dispatch()


class Completer(object):

    def __init__(self, env_loader, completer):
        self.env_loader = env_loader
        self.completer = completer

    def __call__(self, **kwargs):
        if self.env_loader:
            env = self.env_loader()
            return self.completer(env, **kwargs)
        else:
            return self.completer(**kwargs)
