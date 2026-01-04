import datetime
import os
import shutil
from dataclasses import MISSING, fields, is_dataclass

# Project information
now = datetime.date.today()

project = "PyJobShop"
authors = "Leon Lan"
copyright = f"2023 - {now.year}, {authors}"

print("Copying example notebooks into docs/source/examples/")
shutil.copytree("../../examples", "examples/", dirs_exist_ok=True)


# -- General configuration
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_immaterial",
    "nbsphinx",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]

add_module_names = False
python_use_unqualified_type_names = True

# -- API documentation
autodoc_member_order = "bysource"
autodoc_preserve_defaults = True

# -- sphinx-autodoc-typehints
typehints_use_signature = True
typehints_use_signature_return = True
typehints_document_rtype = False

# -- intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}
intersphinx_disabled_domains = ["std"]

# -- nbsphinx
skip_notebooks = os.getenv("SKIP_NOTEBOOKS", False)
nbsphinx_execute = "never" if skip_notebooks else "always"


# -- custom
def autodoc_process_signature(
    app, what, name, obj, options, signature, return_annot
):
    """
    Process signature of dataclasses with default factories, so that sensible
    default values are shown intead of complicated factory references.
    """
    if what != "class" or not is_dataclass(obj) or not signature:
        return None

    for field in fields(obj):
        if field.default_factory is MISSING:
            continue

        # Get the default value from the default factory. By default, we use
        # show the repr(), unless it's a dataclass.
        default = field.default_factory()
        display = repr(default)

        if is_dataclass(default):
            # For dataclasses, show a minimal repr with only non-default
            # fields. E.g., Objective(weight_makespan=1) instead of
            # Objective(weight_makespan=1, weight_tardy_jobs=0, ...).
            parts = []
            for f in fields(default):
                value = getattr(default, f.name)

                # Skip fields that are at their default value.
                is_default = f.default is not MISSING and value == f.default
                is_factory_default = (
                    f.default_factory is not MISSING
                    and value == f.default_factory()
                )
                if is_default or is_factory_default:
                    continue

                parts.append(f"{f.name}={value!r}")

            display = f"{type(default).__name__}({', '.join(parts)})"

        signature = signature.replace("<factory>", display, 1)

    return signature, return_annot


def setup(app):
    app.connect(
        "autodoc-process-signature", autodoc_process_signature, priority=0
    )
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_immaterial"
html_theme_options = {
    "repo_url": "https://github.com/PyJobShop/PyJobShop/",
    "icon": {
        "repo": "fontawesome/brands/github",
        "edit": "material/file-edit-outline",
    },
    "features": [
        "navigation.expand",
        "navigation.top",
        "navigation.sections",
        "navigation.tracking",
        "content.code.copy",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "primary": "indigo",
            "accent": "purple",
            "scheme": "default",
            "toggle": {
                "icon": "material/lightbulb-outline",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "primary": "indigo",
            "accent": "purple",
            "scheme": "slate",
            "toggle": {
                "icon": "material/lightbulb",
                "name": "Switch to light mode",
            },
        },
    ],
}

object_description_options = [
    (
        "py:.*",
        {"include_fields_in_toc": False, "include_rubrics_in_toc": False},
    ),
    ("py:attribute", {"include_in_toc": False}),
    ("py:parameter", {"include_in_toc": False}),
]
