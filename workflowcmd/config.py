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
import json as _json

import yaml
import argh
from path import path

from dsl_parser import functions as dsl_functions
from cloudify.workflows import local

from workflowcmd import output, module

WORKFLOWCMD_CONF_PATH = 'WORKFLOWCMD_CONF_PATH'


def _workflowcmd_conf_path():
    return os.path.expanduser(os.environ.get(WORKFLOWCMD_CONF_PATH,
                                             '~/.workflowcmd'))


def _read_workflowcmd_conf():
    conf_path = _workflowcmd_conf_path()
    if not os.path.exists(conf_path):
        return {}
    with open(conf_path) as f:
        return yaml.safe_load(f)


def _update_workflowcmd_conf(conf):
    current_conf = _read_workflowcmd_conf()
    current_conf.update(conf)
    conf_path = _workflowcmd_conf_path()
    with open(conf_path, 'w') as f:
        return yaml.safe_dump(current_conf, f)


class Loader(object):

    _name = '.local'

    def __init__(self, package, config_path):
        package_path = path(package.__file__).dirname()
        config_path = package_path / config_path
        config_dir = config_path.dirname()
        self.config = yaml.load(config_path.text())
        self.blueprint_path = config_dir / self.config['blueprint_path']
        self.blueprint_dir = self.blueprint_path.dirname()
        self._parser = argh.ArghParser()
        self._parse_setup_command(setup=self.config['setup'])
        storage_dir = _read_workflowcmd_conf().get(
            self.config['name'], {}).get('storage_dir')
        if storage_dir:
            self.storage_dir = path(storage_dir)
            self._parse_commands(commands=self.config['commands'])
            self._parser.add_commands(functions=[self._init_command,
                                                 self._outputs_command])
        else:
            self.storage_dir = None

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
            parameters = self._parse_parameters(
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
        self._add_args_to_func(func, command.get('args', []))
        return func

    def _load_env(self):
        return local.load_env(name=self._name, storage=self._storage())

    def _storage(self):
        return local.FileStorage(storage_dir=self.storage_dir)

    def _parse_setup_command(self, setup):
        @argh.expects_obj
        @argh.named('setup')
        def func(args):
            storage_dir = args.storage_dir or os.getcwd()
            self.storage_dir = path(storage_dir)
            _update_workflowcmd_conf(
                {self.config['name']: {'storage_dir': storage_dir}})
            with open(self.blueprint_path) as f:
                blueprint = yaml.safe_load(f)
            inputs = {key: value.get('default', '_')
                      for key, value in blueprint.get('inputs').items()}
            inputs.update(self._parse_parameters(
                parameters=setup.get('inputs', {}),
                args=vars(args)))
            inputs_path = self.storage_dir / 'inputs.yaml'
            inputs_path.write_text(yaml.safe_dump(inputs,
                                                  default_flow_style=False))
            after_setup_func = setup.get('after_setup')
            if after_setup_func:
                after_setup = module.load_attribute(after_setup_func)
                after_setup(self)

        self._add_args_to_func(func, setup.get('args', []))
        argh.arg('-s', '--storage_dir')(func)
        self._parser.add_commands(functions=[func])

    @argh.named('init')
    def _init_command(self, reset=False):
        local_dir = self.storage_dir / self._name
        if local_dir.exists() and reset:
            shutil.rmtree(local_dir)
        with open(self.storage_dir / 'inputs.yaml') as f:
            inputs = yaml.safe_load(f)
        sys.path.append(self.blueprint_dir)
        local.init_env(blueprint_path=self.blueprint_path,
                       inputs=inputs,
                       name=self._name,
                       storage=self._storage(),
                       ignored_modules=self.config.get('ignored_modules', []))

    @argh.named('outputs')
    def _outputs_command(self, json=False):
        outputs = self._load_env().outputs()
        if json:
            return _json.dumps(outputs, sort_keys=True, indent=2)
        else:
            return yaml.safe_dump(outputs, default_flow_style=False)

    def _add_args_to_func(self, func, args):
        for arg in reversed(args):
            name = arg.pop('name')
            completer = arg.pop('completer', None)
            if completer:
                completer = module.load_attribute(completer)
                completer = Completer(self._load_env, completer)
                arg['completer'] = completer
            name = name if isinstance(name, list) else [name]
            argh.arg(*name, **arg)(func)

    def _parse_parameters(self, parameters, args):
        functions = {
            'arg': lambda func_args: args[func_args],
            'env': lambda func_args: os.environ[func_args],
            'loader': lambda func_args: getattr(self, func_args)
        }
        for name, process in functions.items():
            dsl_functions.register(_function(process), name)
        try:
            return dsl_functions.evaluate_functions(parameters,
                                                    None, None, None, None)
        finally:
            for name in functions.keys():
                dsl_functions.unregister(name)

    def dispatch(self):
        self._parser.dispatch()


def dispatch(package, config_path):
    loader = Loader(package=package, config_path=config_path)
    loader.dispatch()


def _function(process):
    class Function(dsl_functions.Function):
        validate = None
        evaluate = None
        function_args = None

        def parse_args(self, args):
            self.function_args = args

        def evaluate_runtime(self, **_):
            return process(self.function_args)
    return Function


class Completer(object):

    def __init__(self, env_loader, completer):
        self.env_loader = env_loader
        self.completer = completer

    def __call__(self, **kwargs):
        env = self.env_loader()
        return self.completer(env, **kwargs)
