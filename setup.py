from setuptools import find_packages, setup

setup(
    name="pyjobshop",
    version="0.0.2b",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pyjobshop=pyjobshop.cli:main",
        ],
    },
)
