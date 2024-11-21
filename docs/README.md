# Documentation

This directory hosts the documentation. 
We use Sphinx for this.
If you want to build the documentation, you need to install a few unique dependencies that are listed in the development dependencies group in the top-level `pyproject.toml`.
You can install those dependencies using `uv sync --all-groups`.

The Makefile in this directory can be used to build the documentation.

Running the command `uv run make help` from this directory provides an overview of the available options.
In particular `uv run make html` is useful, as that will build the documentation in the exact same way as it will be displayed on the website later.

> Alternatively, one can run `uv run make html --directory=docs` from the project root as well.

Finally, all Sphinx-related settings are configured in `docs/source/conf.py`.

## Skipping the example notebooks

The example notebooks are all executed by default when building the documentation.
This can take a long time, so it is possible to skip execution when building the documentation locally.
To do so, simply set the `SKIP_NOTEBOOKS` environmental variable when building the documentation, like so
```
SKIP_NOTEBOOKS=1 uv run make html
```
