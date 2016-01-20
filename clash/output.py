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

import colors

from cloudify import logs

from clash import module

_task_event_color = {
    'workflow_started': 13,
    'task_succeeded': 10,
    'task_failed': 9,
    'task_rescheduled': 11,
    'sending_task': 14,
    'task_started': 13,
    'workflow_failed': 9,
    'workflow_succeeded': 10,
}


_log_level_color = {
    'warn': 'yellow',
    'warning': 'yellow',
    'error': 'red',
    'info': 'green'
}


class Event(dict):

    def __init__(self, event):
        self.update(event)

    def __str__(self):
        operation = self.operation
        if operation:
            operation = operation.split('.')[-1]
            operation = colors.magenta(operation)
        if self.source_node_name:
            source_name = colors.cyan(self.source_node_name)
            target_name = colors.cyan(self.target_node_name)
            context = '{}->{}|{}'.format(source_name, target_name, operation)
        elif self.node_name:
            node_name = colors.cyan(self.node_name)
            context = node_name
            if operation:
                context = '{}.{}'.format(node_name, operation)
        else:
            context = colors.cyan(self.workflow_id)
        message = colors.color(
            self.message,
            fg=_task_event_color.get(self.event_type, 15))
        if self.level:
            level = colors.color(
                self.level.upper(),
                fg=_log_level_color.get(self.level, 15))
            message = '{}: {}'.format(level, message)
        return '[{}] {}'.format(context, message)

    @property
    def context(self):
        return self.get('context', {})

    @property
    def blueprint_id(self):
        return self.context.get('blueprint_id')

    @property
    def deployment_id(self):
        return self.context.get('deployment_id')

    @property
    def execution_id(self):
        return self.context.get('execution_id')

    @property
    def workflow_id(self):
        return self.context.get('workflow_id')

    @property
    def task_id(self):
        return self.context.get('task_id')

    @property
    def task_name(self):
        return self.context.get('task_name')

    @property
    def task_target(self):
        return self.context.get('task_target')

    @property
    def operation(self):
        return self.context.get('operation')

    @property
    def plugin(self):
        return self.context.get('plugin')

    @property
    def node_instance_id(self):
        return self.context.get('node_id')

    @property
    def node_id(self):
        return self.node_name

    @property
    def node_name(self):
        return self.context.get('node_name')

    @property
    def source_node_instance_id(self):
        return self.context.get('source_id')

    @property
    def source_node_id(self):
        return self.source_node_id

    @property
    def source_node_name(self):
        return self.context.get('source_name')

    @property
    def target_node_instance_id(self):
        return self.context.get('target_id')

    @property
    def target_node_id(self):
        return self.target_node_name

    @property
    def target_node_name(self):
        return self.context.get('target_name')

    @property
    def logger(self):
        return self.get('logger')

    @property
    def level(self):
        return self.get('level')

    @property
    def message(self):
        return self.get('message', {}).get('text', '').encode('utf-8')

    @property
    def timestamp(self):
        return self.get('@timestamp') or self.get('timestamp')

    @property
    def message_code(self):
        return self.get('message_code')

    @property
    def type(self):
        return self.get('type')

    @property
    def event_type(self):
        return self.get('event_type')

    @property
    def task_current_retries(self):
        return self.context.get('task_current_retries')

    @property
    def task_total_retries(self):
        return self.context.get('task_total_retries')


def setup_output(event_cls, verbose, env, command):
    if event_cls is None:
        event_cls = Event
    else:
        event_cls = module.load_attribute(event_cls)
        if hasattr(event_cls, 'factory'):
            event_cls = event_cls.factory(env=env,
                                          verbose=verbose,
                                          command=command)
    logs.EVENT_CLASS = event_cls

    if not verbose:
        def stub(*_):
            pass
        logs.stdout_event_out = stub
