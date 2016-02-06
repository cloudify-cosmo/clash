macros.yaml
===========

When an environment is created using ``<MY_APP> env create``, a file named
``macros.yaml`` is generated in the storage dir.

This file enables users of your application to extend the application by adding
new commands in the form of macros.

A macro definition specifies the arguments it accepts and the list of commands
to execute.

To explain the usage, we'll use `clue <https://clue.readthedocs.org>`_ as
reference, which at the time of writing, is the only framework known to make
use of ``clash``.

``clue`` exposes several subcommands under the ``git`` namespace. The following
example shows how a user may extend this namespace to simplify the process of
preparing a pull request.

``macros.yaml`` example:

.. code-block:: yaml

    git:
      prepare-pull-request:
        args:
        - name: branch_set
          completer: clue.completion:branches_completer
        commands:
        - name: git.checkout
          args:
          - func:
              name: scripts.git:get_base
              kwargs:
                branch_set: { arg: branch_set }
        - name: git.pull
        - name: git.checkout
          args: [{ arg: branch_set }]
        - name: git.squash
        - name: git.rebase
        - name: git.status
          args: [--active]

The above exposes a new command that can be called like this:

.. code-block:: sh

    $ clue git prepare-pull-request my_branch_set

which is roughly equivalent to:

.. code-block:: sh

    $ # the actual macro reads the base property from branch_set definition
    $ clue git checkout master
    $ clue git pull
    $ clue git checkout my_branch_set
    $ clue git squash
    $ clue git rebase
    $ clue git status --active


Name Transformations
--------------------
``git pull`` should be written as ``git.pull`` in the commands definition,
arguments passed to commands should be passed as a list of arguments to passed
in command line syntax.

Completion
----------
The ``branch_set`` arg definition re-uses the bash completer
``clue.completion:branches_completer`` provided by ``clue``.

Namespace
---------
The ``git`` namespace is extended to include a new ``prepare-pull-request``
subcommand. We could have also added a new top level command:

.. code-block:: yaml

    # omitting the top level git namespace
    prepare-pull-request:
      ..

or create a new namespaces:

.. code-block:: yaml

    my-macros:
      prepare-pull-request:
        ..

which could then be called like this:

.. code-block:: sh

    $ clue my-macros prepare-pull-request my_branch_set

Intrinsic Functions
-------------------
Intrinsic functions can be used to build complex arguments. In the previous
example, we used the ``arg`` intrinsic function to read the argument provided
to the ``prepare-pull-request`` macro, and the ``func`` intrinsic function
which can be used to implement use defined intrinsic functions.

Additional built-in intrinsic functions include:

* ``env`` to read environment variables. (Value can be a string or a list of two
  elements in which the second element will be a default value)
* ``concat`` to concatenate strings. (value is a list of elements to concatenate)
* ``loader`` and ``user_config`` to read attribute from ``clash`` defined objects.
