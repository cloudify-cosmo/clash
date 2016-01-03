import sys
import os
import shutil
import json as _json

import yaml
import argh
from path import path

from dsl_parser import functions as dsl_functions
from cloudify.workflows import local
from cloudify_cli import utils as cli_utils

from workflowcmd import output, util


def _global_cdev_conf_path():
    return os.path.expanduser(os.environ.get('CDEV_CONF_PATH', '~/.cdev'))


def _read_global_cdev_conf():
    cdev_conf_path = _global_cdev_conf_path()
    if not os.path.exists(cdev_conf_path):
        return {}
    with open(cdev_conf_path) as f:
        return yaml.safe_load(f)


def _update_global_cdev_conf(conf):
    cdev_conf_path = _global_cdev_conf_path()
    with open(cdev_conf_path, 'w') as f:
        return yaml.safe_dump(conf, f)


class Loader(object):

    _name = '.local'

    def __init__(self, package, config_path):
        package_path = path(package.__file__).dirname()
        config_path = package_path / config_path
        config_dir = config_path.dirname()
        self._config = yaml.load(config_path.text())
        self._blueprint_path = config_dir / self._config['blueprint_path']
        self._blueprint_dir = self._blueprint_path.dirname()
        self._parser = argh.ArghParser()

        self._parser.add_commands(functions=[self._setup_command])
        storage_dir = _read_global_cdev_conf().get('storage_dir')
        if storage_dir:
            self._storage_dir = path(storage_dir)
            self._parse_commands(commands=self._config['commands'])
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
            parameters = _parse_parameters(command.get('parameters', {}),
                                           vars(args))
            task_config = {
                'retries': 0,
                'retry_interval': 1,
                'thread_pool_size': 1
            }
            global_task_config = self._config.get('task', {})
            command_task_config = command.get('task', {})
            task_config.update(global_task_config)
            task_config.update(command_task_config)
            sys.path.append(self._storage_dir / self._name / 'resources')
            env = self._load_env()

            event_cls = command.get('event_cls',
                                    self._config.get('event_cls'))
            output.setup_output(event_cls=event_cls,
                                verbose=args.verbose,
                                env=env)

            env.execute(workflow=command['workflow'],
                        parameters=parameters,
                        task_retries=task_config['retries'],
                        task_retry_interval=task_config['retry_interval'],
                        task_thread_pool_size=task_config['thread_pool_size'])

        for arg in reversed(command.get('args', [])):
            name = arg.pop('name')
            completer = arg.pop('completer', None)
            if completer:
                completer = util.load_attribute(completer)
                completer = Completer(self._load_env, completer)
                arg['completer'] = completer
            name = name if isinstance(name, list) else [name]
            argh.arg(*name, **arg)(func)

        return func

    def _load_env(self):
        return local.load_env(name=self._name, storage=self._storage())

    def _storage(self):
        return local.FileStorage(storage_dir=self._storage_dir)

    @argh.named('setup')
    def _setup_command(self, storage_dir):
        self._storage_dir = path(storage_dir)
        _update_global_cdev_conf({'storage_dir': storage_dir})
        with open(self._blueprint_path) as f:
            blueprint = yaml.safe_load(f)
        inputs = {key: value.get('default', '_')
                  for key, value in blueprint.get('inputs').items()}
        inputs_path = self._storage_dir / 'inputs.yaml'
        inputs_path.write_text(yaml.safe_dump(inputs,
                                              default_flow_style=False))

    @argh.named('init')
    def _init_command(self, reset=False):
        local_dir = self._storage_dir / self._name
        if local_dir.exists() and reset:
            shutil.rmtree(local_dir)
        inputs = cli_utils.inputs_to_dict(self._storage_dir / 'inputs.yaml',
                                          'inputs')
        sys.path.append(self._blueprint_dir)
        local.init_env(blueprint_path=self._blueprint_path,
                       inputs=inputs,
                       name=self._name,
                       storage=self._storage(),
                       ignored_modules=self._config.get('ignored_modules', []))

    @argh.named('outputs')
    def _outputs_command(self, json=False):
        outputs = self._load_env().outputs()
        if json:
            return _json.dumps(outputs, sort_keys=True, indent=2)
        else:
            return yaml.safe_dump(outputs, default_flow_style=False)

    def dispatch(self):
        self._parser.dispatch()


def dispatch(package, config_path):
    loader = Loader(package=package, config_path=config_path)
    loader.dispatch()


def _parse_parameters(parameters, args):
    functions = {
        'arg': lambda func_args: args[func_args],
        'env': lambda func_args: os.environ[func_args]
    }
    for name, process in functions.items():
        dsl_functions.register(_function(process), name)
    try:
        return dsl_functions.evaluate_functions(parameters,
                                                None, None, None, None)
    finally:
        for name in functions.keys():
            dsl_functions.unregister(name)


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
