# Documentation

This directory hosts the documentation. The site is built with Zensical from
Markdown files in `docs/source/`.

Install the development and documentation dependencies from the project root:

```shell
uv sync --all-groups
```

Build the documentation from this directory:

```shell
uv run make html
```

The full build executes the example notebooks from the repository-level
`examples/` directory, converts them to Markdown in `docs/source/examples/`,
and then runs `zensical build`.

For faster local iteration, convert notebooks without executing them:

```shell
uv run make fast
```

To preview the site locally, run:

```shell
uv run make serve
```
