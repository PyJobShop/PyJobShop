import datetime
import os
import shutil

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
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_immaterial",
    "nbsphinx",
    "numpydoc",
]

templates_path = ["_templates"]

add_module_names = False
python_use_unqualified_type_names = True

# -- API documentation
autoclass_content = "class"
autodoc_member_order = "bysource"
autodoc_typehints = "signature"
autodoc_preserve_defaults = True

# -- numpydoc
numpydoc_xref_param_type = True
numpydoc_class_members_toctree = False
numpydoc_attributes_as_param_list = False
napoleon_include_special_with_doc = True


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


# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_immaterial"
html_static_path = ["_static"]

html_theme_options = {
    "repo_url": "https://github.com/leonlan/PyJobShop/",
    "icon": {
        "repo": "fontawesome/brands/github",
        "edit": "material/file-edit-outline",
    },
    "features": [
        "navigation.expand",
        "navigation.top",
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
