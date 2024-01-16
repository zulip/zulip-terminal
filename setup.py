import codecs
import os

from setuptools import find_packages, setup

from zulipterminal.version import ZT_VERSION


def long_description():
    if not (os.path.isfile("README.md") and os.access("README.md", os.R_OK)):
        return ""

    with codecs.open("README.md", encoding="utf8") as f:
        source = f.read()

        # Skip first line (assumed to have title) to reduce duplication
        return "\n".join(source.splitlines()[1:])


testing_minimal_deps = [
    "pytest~=7.2.0",
    "pytest-mock~=3.10.0",
]

testing_plugin_deps = [
    "pytest-cov~=4.0.0",
]

testing_deps = testing_minimal_deps + testing_plugin_deps

linting_deps = [
    "isort~=5.11.0",
    "black~=23.0",
    "ruff==0.0.267",
    "codespell[toml]~=2.2.5",
    "typos~=1.16.11",
]

typing_deps = [
    "lxml-stubs",
    "mypy~=1.3.0",
    "types-beautifulsoup4",
    "types-pygments",
    "types-python-dateutil",
    "types-tzlocal",
    "types-pytz",
    "types-requests",
]

dev_helper_deps = [
    "pudb==2022.1.1",
    "snakeviz>=2.1.1",
    "gitlint~=0.18.0",
]

setup(
    name="zulip-term",
    version=ZT_VERSION,
    description="Zulip's official terminal client",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/zulip/zulip-terminal",
    author="Zulip Open Source Project",
    author_email="zulip-devel@googlegroups.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    project_urls={
        "Changelog": "https://github.com/zulip/zulip-terminal/blob/main/CHANGELOG.md",
        "FAQs": "https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md",
        "Issues": "https://github.com/zulip/zulip-terminal/issues",
        "Hot Keys": "https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md",
    },
    python_requires=">=3.7, <3.12",
    keywords="",
    packages=find_packages(exclude=["tests", "tests.*"]),
    zip_safe=True,
    entry_points={
        "console_scripts": [
            "zulip-term = zulipterminal.cli.run:main",
            "zulip-term-check-symbols = zulipterminal.scripts.render_symbols:main",
        ],
    },
    extras_require={
        "dev": testing_deps + linting_deps + typing_deps + dev_helper_deps,
        "testing": testing_deps,
        "testing_minimal": testing_minimal_deps,
        "linting": linting_deps,
        "typing": typing_deps,
    },
    tests_require=testing_deps,
    install_requires=[
        "urwid~=2.1.2",
        "zulip>=0.8.2",
        "urwid_readline>=0.13",
        "beautifulsoup4>=4.11.1",
        "lxml~=4.9.2",
        "pygments>=2.14.0,<2.18.0",
        "typing_extensions~=4.5.0",
        "python-dateutil>=2.8.2",
        "pytz>=2022.7.1",
        "tzlocal>=2.1",
        "pyperclip>=1.8.1",
    ],
)
