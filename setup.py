import os
import sys
import codecs
from setuptools import setup, find_packages
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
        return f.read()


testing_deps = [
    'pytest==3.10.1',
    'pytest-cov==2.5.1',
    'pytest-mock==1.7.1',
    'pytest-pep8==1.0.6',
]

dev_helper_deps = [
    'mypy==0.740',
    'pudb==2017.1.4',
    'snakeviz==0.4.2',
    'gitlint>=0.10',
]

setup(
    name='zulip-term',
    version=ZT_VERSION,
    description='A terminal-based interface to zulip chat',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/zulip/zulip-terminal',
    author='Zulip',
    author_email='zulip-devel@googlegroups.com',
    license='MIT',
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
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    python_requires='>=3.5, <=3.8',
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
        'dev': testing_deps + dev_helper_deps,
    },
    tests_require=testing_deps,
    install_requires=[
        'urwid==2.0.1',
        'zulip==0.6.3',
        'emoji==0.5.0',
        'urwid_readline==0.10',
        'beautifulsoup4==4.6.0',
        'lxml==4.2.3',
        'mypy_extensions>=0.4',
    ],
)
