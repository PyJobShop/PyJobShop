from setuptools import find_packages, setup

setup(
    name="pyjobshop",
    version="0.0.2a",
    packages=find_packages(include=["pyjobshop"]),
    entry_points={
        "console_scripts": [
            "pyjobshop=pyjobshop.cli:main",
        ],
    },
)
