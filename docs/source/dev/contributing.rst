Contributing
============

Conversations about development and issues take place in the `GitHub repository <https://github.com/PyJobShop/PyJobShop/>`_.
Feel free to open a new issue if you have something to discuss.
We welcome contributions from the community.

Before starting work on a new feature or significant change, please open an issue or start a discussion first.
This helps us determine whether the feature fits the project and align on the approach.
We're happy to help you get started, review early drafts, or discuss implementation details.
The requirements below describe what's needed before a PR can be merged, but don't let them discourage you from getting started.


Setting up a local installation
-------------------------------

Start by forking the PyJobShop repository from `GitHub <https://github.com/PyJobShop/PyJobShop/fork>`_.
Then, clone your new fork to some local environment:

.. code-block:: shell

   git clone https://github.com/<your username>/PyJobShop.git

Now, change into the PyJobShop directory, and set-up the virtual environment using `uv <https://github.com/astral-sh/uv>`_ (v0.5.4 or above):

.. code-block:: shell

   cd PyJobShop
   uv sync --all-extras --all-groups

Now make sure everything runs smoothly, by executing the test suite:

.. code-block:: shell

   uv run pytest

.. note::

   By default, tests will run on all solvers, which are currently OR-Tools and CP Optimizer.
   If you encounter installation issues with CP Optimizer, you can also run tests only for OR-Tools by specifying the ``--solvers`` argument as follows:

   .. code-block:: shell

      uv run pytest --solvers ortools

   See the :doc:`installation instructions<../setup/installation>` page for more details about installing CP Optimizer.

.. note::

   If you use `pre-commit <https://pre-commit.com/>`_, you can use our pre-commit configuration file to set that up too.
   Simply type:

   .. code-block:: shell

      uv run pre-commit install

   After this completes, style and typing issues are automatically checked whenever you make a new commit to your feature branch.
   To manually run pre-commit over all your files, you can run the following command:

   .. code-block:: shell

      uv run pre-commit run --all-files


Committing changes
------------------

We use pull requests to develop PyJobShop.
The following guidelines help us maintain the codebase.
Don't worry if your first pull request doesn't meet all of these requirements.

- **One branch. One feature.**
  Branches are cheap and GitHub makes it easy to merge and delete branches with a few clicks.
  Avoid the temptation to lump in a bunch of unrelated changes when working on a feature, if possible.
  This helps us keep track of what has changed when preparing a release.
- Before merging, code submissions should include tests.
  If you're unsure how to write tests for your changes, feel free to open a draft PR and ask for guidance.
- Each function, class, method, and attribute needs to be documented using docstrings.
  We conform to the `NumPy docstring standard <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_.
- If you are adding new functionality, you need to add it to the documentation by editing (or creating) the appropriate file in ``docs/source/``.
- Make sure your documentation changes parse correctly.
  See the documentation in the ``docs/`` directory for details on how to build the documentation locally.

.. note::

   Please use the "Pull request" template on GitHub when opening a pull request.
   Feel free to open a draft pull request early, even if your work is incomplete.
   This allows us to provide feedback and help you iterate.


Licensing
---------

PyJobShop is licensed under the MIT license.
All code, documentation and other files added to PyJobShop by contributors is licensed under this license, unless another license is explicitly specified in the source file.
For your contribution, please check that it can be included into PyJobShop under the MIT license.
If you did not write the code yourself, you must ensure that the existing license is compatible and include the license information in the contributed files, or obtain permission from the original author to relicense the contributed code.
Contributors keep the copyright for code they wrote and submit for inclusion to PyJobShop.
