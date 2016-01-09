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

import sys
import os
import shutil
import tempfile
import json as _json
import StringIO

import yaml
import argh
from path import path

from cloudify.workflows import local

from clash import output
from clash import functions
from clash import module
from clash import config


class Loader(object):

    _name = '.local'

    def __init__(self, config_path):
        config_path = path(config_path)
        config_dir = config_path.dirname()
        self.config = _json.loads(_json.dumps(yaml.safe_load(
            config_path.text())))
        self.blueprint_path = config_dir / self.config['blueprint_path']
        self.blueprint_path = self.blueprint_path.abspath()
        self.blueprint_dir = self.blueprint_path.dirname()
        self._parser = argh.ArghParser()
        self._parse_setup_command(setup=self.config.get('setup', {}))
        self.storage_dir = config.get_storage_dir(self.config)
        if self.storage_dir:
            self._parse_commands(commands=self.config.get('commands', {}))
            self._parser.add_commands(functions=[self._init_command,
                                                 self._outputs_command])

    def _parse_commands(self, commands, namespace=None):
        functions = []
        for name, command in commands.items():
            if 'workflow' not in command:
                self._parse_commands(commands=command, namespace=name)
                continue
            functions.append(self._parse_command(name=name, command=command))
        self._parser.add_commands(functions=functions, namespace=namespace)

    def _parse_command(self, name, command):
        @argh.expects_obj
        @argh.named(name)
        @argh.arg('-v', '--verbose', default=False)
        def func(args):
            bin_dir = path(sys.executable).dirname()
            current_path_env = os.environ.get('PATH', '')
            if bin_dir not in current_path_env:
                os.environ['PATH'] = '{}{}{}'.format(bin_dir,
                                                     os.pathsep,
                                                     current_path_env)
            parameters = functions.parse_parameters(
                loader=self,
                parameters=command.get('parameters', {}),
                args=vars(args))
            task_config = {
                'retries': 0,
                'retry_interval': 1,
                'thread_pool_size': 1
            }
            global_task_config = self.config.get('task', {})
            command_task_config = command.get('task', {})
            task_config.update(global_task_config)
            task_config.update(command_task_config)
            sys.path.append(self.storage_dir / self._name / 'resources')
            env = self._load_env()

            event_cls = command.get('event_cls',
                                    self.config.get('event_cls'))
            output.setup_output(event_cls=event_cls,
                                verbose=args.verbose,
                                env=env)

            env.execute(workflow=command['workflow'],
                        parameters=parameters,
                        task_retries=task_config['retries'],
                        task_retry_interval=task_config['retry_interval'],
                        task_thread_pool_size=task_config['thread_pool_size'])
        self._add_args_to_func(func, command.get('args', []), skip_env=False)
        return func

    def _load_env(self):
        return local.load_env(name=self._name, storage=self._storage())

    def _storage(self):
        return local.FileStorage(storage_dir=self.storage_dir)

    def _parse_setup_command(self, setup):
        @argh.expects_obj
        @argh.named('setup')
        def func(args):
            if self.storage_dir and not args.reset:
                raise argh.CommandError('storage dir already configured. pass '
                                        '--reset to override.')
            storage_dir = args.storage_dir or os.getcwd()
            self.storage_dir = path(storage_dir)
            self.storage_dir.mkdir_p()
            config.update_storage_dir(self.config, storage_dir)
            config.update_editable(self.config, args.editable)
            with open(self.blueprint_path) as f:
                blueprint = yaml.safe_load(f) or {}
            inputs = {key: value.get('default', '_')
                      for key, value in blueprint.get('inputs', {}).items()}
            inputs.update(functions.parse_parameters(
                loader=self,
                parameters=setup.get('inputs', {}),
                args=vars(args)))
            inputs_path = self.storage_dir / 'inputs.yaml'
            inputs_path.write_text(yaml.safe_dump(inputs,
                                                  default_flow_style=False))
            after_setup_func = self.config.get('hooks', {}).get('after_setup')
            if after_setup_func:
                after_setup = module.load_attribute(after_setup_func)
                after_setup(self, **vars(args))

        self._add_args_to_func(func, setup.get('args', []), skip_env=True)
        argh.arg('-s', '--storage-dir')(func)
        argh.arg('-r', '--reset', default=False)(func)
        argh.arg('-e', '--editable', default=False)(func)
        self._parser.add_commands(functions=[func])

    @argh.named('init')
    def _init_command(self, reset=False):
        local_dir = self.storage_dir / self._name
        if local_dir.exists():
            if reset:
                shutil.rmtree(local_dir)
            else:
                raise argh.CommandError('Already initialized, pass --reset '
                                        'to re-initialize.')
        with open(self.storage_dir / 'inputs.yaml') as f:
            inputs = yaml.safe_load(f) or {}
        temp_dir = path(tempfile.mkdtemp(
            prefix='{}-blueprint-dir-'.format(self.config['name'])))
        blueprint_dir = temp_dir / 'blueprint'
        try:
            shutil.copytree(self.blueprint_dir, blueprint_dir)
            sys.path.append(blueprint_dir)
            blueprint_path = blueprint_dir / self.blueprint_path.basename()
            before_init_func = self.config.get('hooks', {}).get('before_init')
            if before_init_func:
                blueprint = yaml.safe_load(blueprint_path.text())
                before_init = module.load_attribute(before_init_func)
                before_init(blueprint=blueprint,
                            inputs=inputs,
                            loader=self)
                blueprint_path.write_text(yaml.safe_dump(blueprint))
            ignored_modules = self.config.get('ignored_modules', [])
            local.init_env(blueprint_path=blueprint_path,
                           inputs=inputs,
                           name=self._name,
                           storage=self._storage(),
                           ignored_modules=ignored_modules)
        finally:
            shutil.rmtree(blueprint_dir, ignore_errors=True)
        if config.is_editable(self.config):
            resources_path = self.storage_dir / self._name / 'resources'
            shutil.rmtree(resources_path, ignore_errors=True)
            os.symlink(self.blueprint_dir, resources_path)

    @argh.named('outputs')
    def _outputs_command(self, json=False):
        outputs = self._load_env().outputs()
        if json:
            return _json.dumps(outputs, sort_keys=True, indent=2)
        else:
            return yaml.safe_dump(outputs, default_flow_style=False)

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
