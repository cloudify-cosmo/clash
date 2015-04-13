from setuptools import setup

setup(
    name='workflowcmd',
    version='0.1',
    author='Dan Kilman',
    author_email='dankilman@gmail.com',
    packages=['workflowcmd'],
    description='Turn a Cloudify local blueprint into a CLI',
    zip_safe=False,
    install_requires=[
        'ansicolors',
        'argh',
        'path.py',
        'cloudify>=3.2a8'
    ]
)
