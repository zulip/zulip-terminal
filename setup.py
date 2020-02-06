import os
import sys
import codecs
from shutil import rmtree
from setuptools import setup, find_packages, Command
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
    'pytest==5.3.5',
    'pytest-cov==2.5.1',
    'pytest-mock==1.7.1',
    'pytest-pep8==1.0.6',
    'zipp==1.0.0',  # To support Python 3.5
]

dev_helper_deps = [
    'mypy==0.740',
    'pudb==2017.1.4',
    'snakeviz==0.4.2',
    'gitlint>=0.10',
]


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "build and upload release to test/main server."
    "Read Making a new release wiki of zt on github "
    "for proper guidelines on making a new release."
    user_options = [
        # The format is (long option, short option, description).
        ('final-release=', None,
         'set it to "True" to push the release to the main PyPI server.'
         'This also adds git tags and pushes them upstream.'),
    ]

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        # Make release to test server by default.
        self.final_release = None

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            here = os.path.abspath(os.path.dirname(__file__))
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel distribution…')
        os.system('{0} setup.py sdist bdist_wheel --python-tag=py35.py36.py37'
                  .format(sys.executable))

        if self.final_release == 'True':
            self.status('Uploading the package to PyPI via Twine…')
            os.system('twine upload dist/*')

            self.status('Pushing git tags…')
            os.system('git tag v{0}'.format(ZT_VERSION))
            os.system('git push --tags')
        else:
            self.status('Uploading the package to Test PyPI via Twine…')
            os.system('twine upload --repository-url'
                      ' https://test.pypi.org/legacy/ dist/*')

        sys.exit()

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
    cmdclass={
        'test': PyTest,
        # $ setup.py publish support.
        'upload': UploadCommand
        },
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
        'urwid==2.1.0',
        'zulip==0.6.3',
        'emoji==0.5.0',
        'urwid_readline==0.10',
        'beautifulsoup4==4.6.0',
        'lxml==4.2.3',
        'mypy_extensions>=0.4',
    ],
)
