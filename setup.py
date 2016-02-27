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

from setuptools import setup

setup(
    name='clash',
    version='0.15',
    author='GigaSpaces',
    author_email='cosmo-admin@gigaspaces.com',
    packages=['clash'],
    description='Framework to wrap Cloudify local based blueprints as CLIs',
    license='Apache License, Version 2.0',
    zip_safe=False,
    install_requires=[
        'argcomplete',
        'ansicolors',
        'argh',
        'path.py',
        'cloudify-plugins-common>=3.3.0,<3.4',
        'cloudify-dsl-parser>=3.3.0,<3.4',
        'cloudify-script-plugin>=1.3.0,<1.4'
    ]
)
