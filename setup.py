import codecs
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

from zulipterminal.version import ZT_VERSION


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def long_description():
    if not (os.path.isfile('README.md') and os.access('README.md', os.R_OK)):
        return ''

    with codecs.open('README.md', encoding='utf8') as f:
        source = f.read()

        # Skip first line (assumed to have title) to reduce duplication
        return '\n'.join(source.splitlines()[1:])


testing_deps = [
    'pytest==5.3.5',
    'pytest-cov==2.5.1',
    'pytest-mock==1.7.1',
    'zipp==1.0.0',  # To support Python 3.5
]

linting_deps = [
    'isort==4.3.21',
    'mypy==0.782',
    'flake8~=3.8.3',
    'flake8-quotes~=3.2.0',
    'flake8-continuation~=1.0.5',
]

dev_helper_deps = [
    'pudb==2017.1.4',
    'snakeviz==0.4.2',
    'gitlint>=0.10',
    'autopep8~=1.5.4',
    'autoflake~=1.3.1',
]

setup(
    name='zulip-term',
    version=ZT_VERSION,
    description="Zulip's official terminal client",
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/zulip/zulip-terminal',
    author='Zulip Open Source Project',
    author_email='zulip-devel@googlegroups.com',
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: End Users/Desktop',
        'Topic :: Communications :: Chat',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    project_urls={
        'Changelog':
            'https://github.com/zulip/zulip-terminal/blob/master/CHANGELOG.md',
        'FAQs':
            'https://github.com/zulip/zulip-terminal/blob/master/docs/FAQ.md',
        'Issues':
            'https://github.com/zulip/zulip-terminal/issues',
    },
    python_requires='>=3.5, <3.10',
    keywords='',
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=True,
    cmdclass={'test': PyTest},
    test_suite='test',
    entry_points={
        'console_scripts': [
            'zulip-term = zulipterminal.cli.run:main',
        ],
    },
    extras_require={
        'dev': testing_deps + linting_deps + dev_helper_deps,
        'testing': testing_deps,
        'linting': linting_deps,
    },
    tests_require=testing_deps,
    install_requires=[
        'urwid~=2.1.2',
        'zulip>=0.7.0',
        'urwid_readline>=0.12',
        'beautifulsoup4>=4.9.0',
        'lxml>=4.5.2',
        'typing_extensions>=3.7',
        'python-dateutil>=2.8.1',
        'tzlocal>=2.1',
    ],
)
