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

import unittest
from mock import patch

from cloudify import logs

from clash.output import Event, setup_output

STUB = object()


@patch('cloudify.logs.EVENT_CLASS', STUB)
@patch('cloudify.logs.stdout_event_out', STUB)
class TestSetupOutput(unittest.TestCase):

    def test_no_event_cls(self):
        setup_output(event_cls=None,
                     verbose=False,
                     env=None)
        self.assertIs(logs.EVENT_CLASS, Event)

    def test_event_cls(self):
        setup_output(event_cls='{}:MockEvent'.format(__name__),
                     verbose=False,
                     env=None)
        self.assertIs(logs.EVENT_CLASS, MockEvent)

    def test_event_cls_factory(self):
        setup_output(event_cls='{}:MockEventFactory'.format(__name__),
                     verbose=True,
                     env=STUB)
        self.assertTrue(logs.EVENT_CLASS.r_verbose)
        self.assertIs(logs.EVENT_CLASS.r_env, STUB)

    def test_verbose(self):
        setup_output(event_cls=None,
                     verbose=True,
                     env=None)
        self.assertIs(logs.stdout_event_out, STUB)

    def test_none_verbose(self):
        setup_output(event_cls=None,
                     verbose=False,
                     env=None)
        self.assertIsNot(logs.stdout_event_out, STUB)


class MockEvent(object):
    pass


class MockEventFactory(object):

    @staticmethod
    def factory(env, verbose):
        class Result(object):
            r_env = env
            r_verbose = verbose
        return Result
