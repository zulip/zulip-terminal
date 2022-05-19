# Zulip Terminal - [Zulip](https://zulip.com)'s official terminal client

[Recent changes](https://github.com/zulip/zulip-terminal/blob/main/CHANGELOG.md) | [Configuration](#Configuration) | [Hot Keys](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md) | [FAQs](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md) | [Development](#contributor-guidelines) | [Tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/getting-started.md)

[![Zulip chat](https://img.shields.io/badge/zulip-join_chat-brightgreen.svg)](https://chat.zulip.org/#narrow/stream/206-zulip-terminal)
[![PyPI](https://img.shields.io/pypi/v/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![Python Versions](https://img.shields.io/pypi/pyversions/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![GitHub Actions - Linting & tests](https://github.com/zulip/zulip-terminal/workflows/Linting%20%26%20tests/badge.svg?branch=main)](https://github.com/zulip/zulip-terminal/actions?query=workflow%3A%22Linting+%26+tests%22+branch%3Amain)
[![Coverage status](https://img.shields.io/codecov/c/github/zulip/zulip-terminal/main.svg)](https://app.codecov.io/gh/zulip/zulip-terminal/branch/main)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![Screenshot](https://user-images.githubusercontent.com/9568999/169362381-3c2b19e2-2176-4ad0-bd41-604946432512.png)

## About

Zulip Terminal is the official terminal client for Zulip, providing a [text-based user interface (TUI)](https://en.wikipedia.org/wiki/Text-based_user_interface).

Specific aims include:
* Providing a broadly similar user experience to the Zulip web client, ultimately supporting all of its features
* Enabling all actions to be achieved through the keyboard (see [Hot keys](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md))
* Exploring alternative user interface designs suited to the display and input constraints
* Supporting a wide range of platforms and terminal emulators
* Making best use of available rows/columns to scale from 80x24 upwards (see [Small terminal notes](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#how-small-a-size-of-terminal-is-supported))

Learn how to use Zulip Terminal with our [Tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/getting-started.md).

### Feature status

We consider the client to already provide a fairly stable moderately-featureful everyday-user experience.

The terminal client currently has a number of intentional differences to the Zulip web client:
- Additional and occasionally *different* [Hot keys](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md) to better support keyboard-only navigation; other than directional movement these also include:
  - <kbd>z</kbd> - zoom in/out, between streams & topics, or all private messages & specific conversations
  - <kbd>t</kbd> - toggle view of topics for a stream in left panel (**later adopted for recent topics in web client**)
  - <kbd>#</kbd> - narrow to messages in which you're mentioned (<kbd>@</kbd> is already used)
  - <kbd>f</kbd> - narrow to messages you've starred (are **f**ollowing)
- Not marking additional messages read when the end of a conversation is visible ([FAQ entry](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#when-are-messages-marked-as-having-been-read))
- Emoji and reactions are rendered as text only, for maximum terminal/font compatibility
- Footlinks - footnotes for links (URLs) - make messages readable, while retaining a list of links to cross-reference
- Content previewable in the web client, such as images, are also stored as footlinks

The current development focus is on improving aspects of everyday usage which are more commonly used - to reduce the need for users to temporarily switch to another client for a particular feature.

Current limitations which we expect to only resolve over the long term include support for:
* All operations performed by users with extra privileges (owners/admins)
* Accessing and updating all settings
* Using a mouse/pointer to achieve all actions
* An internationalized UI

For queries on missing feature support please take a look at the [Frequently Asked Questions (FAQs)](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md),
our open [Issues](https://github.com/zulip/zulip-terminal/issues/), or sign up on https://chat.zulip.org and chat with users and developers in the [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) stream!

### Supported platforms
- Linux
- OSX
- WSL (On Windows)

### Supported Server Versions

The minimum server version that Zulip Terminal supports is [`2.1.0`](https://zulip.readthedocs.io/en/latest/overview/changelog.html#zulip-2-1-x-series). It may still work with earlier versions.

### Supported Python Versions

Version 0.6.0 was the last release with support for Python 3.5.

Later releases and the main development branch are currently tested (on Ubuntu) with:
- CPython 3.6-3.10
- PyPy 3.6-3.9

Since our automated testing does not cover interactive testing of the UI, there
may be issues with some Python versions, though generally we have not found
this to be the case.

Please note that generally we limit each release to between a lower and upper
Python version, so it is possible that for example if you have a newer version
of Python installed, then some releases (or `main`) may not install correctly.
In some cases this can give rise to the symptoms in issue #1145.

## Installation

We recommend installing in a dedicated python virtual environment (see below) or using an automated option such as [pipx](https://pypi.python.org/pypi/pipx)

* **Stable** - Numbered stable releases are available on PyPI as the package [zulip-term](https://pypi.python.org/pypi/zulip-term)

  To install, run a command like: `pip3 install zulip-term`

* **Latest** - The latest development version can be installed from the main git repository

  To install, run a command like: `pip3 install git+https://github.com/zulip/zulip-terminal.git@main`

We also provide some sample Dockerfiles to build docker images in [docker/](https://github.com/zulip/zulip-terminal/tree/main/docker).

### Installing into an isolated Python virtual environment

With the python 3.6+ required for running, the following should work on most systems:
1. `python3 -m venv zt_venv` (creates a virtual environment named `zt_venv` in the current directory)
2. `source zt_venv/bin/activate` (activates the virtual environment; this assumes a bash-like shell)
3. Run one of the install commands above, 

If you open a different terminal window (or log-off/restart your computer), you'll need to run **step 2** of the above list again before running `zulip-term`, since that activates that virtual environment. You can read more about virtual environments in the [Python 3 library venv documentation](https://docs.python.org/3/library/venv.html).

### Keeping your install up to date

Stable releases are made available on PyPI and GitHub; to ensure you keep up to date with them we suggest checking those sites for updates.
Stable releases are also announced in the #**announce** stream on the Zulip Community server (https://chat.zulip.org), where you are welcome to make an account; future releases are expected to be announced in #**announce>terminal releases**.

If running from the `main` git branch, note that this does not automatically update, and you must do so manually.
This also applies to other source or development installs, including eg. https://aur.archlinux.org/packages/python-zulip-term-git/

## Running for the first time

Upon first running `zulip-term` it looks for a `zuliprc` file, by default in your home directory, which contains the details to log into a Zulip server.

If it doesn't find this file, you have two options:

1. `zulip-term` will prompt you for your server, email and password, and create a `zuliprc` file for you in that location

   **NOTE:** If you use Google, Github or another external authentication to access your Zulip organization then you likely won't have a password set and currently need to create one to use zulip-terminal. If your organization is on Zulip cloud, you can visit https://zulip.com/accounts/go?next=/accounts/password/reset to create a new password for your account. For self-hosted servers please go to your `<Organization URL>/accounts/password/reset/` (eg: https://chat.zulip.org/accounts/password/reset/) to create a new password for your account.

2. Each time you run `zulip-term`, you can specify the path to an alternative `zuliprc` file using the `-c` or `--config-file` options, eg. `$ zulip-term -c /path/to/zuliprc`

   Your personal zuliprc file can be obtained from Zulip servers in your account settings in the web application, which gives you all the permissions you have there. Bot zuliprc files can be downloaded from a similar area for each bot, and will have more limited permissions.

**NOTE:** If your server uses self-signed certificates or an insecure connection, you will need to add extra options to the `zuliprc` file manually - see the documentation for the [Zulip python module](https://pypi.org/project/zulip/).

We suggest running `zulip-term` using the `-e` or `--explore` option (in explore mode) when you are trying Zulip Terminal for the first time, where we intentionally do not mark messages as read. Try following along with our [Tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/getting-started.md) to get the hang of things.

## Configuration

The `zuliprc` file contains information to connect to your chat server in the `[api]` section, but also optional configuration for `zulip-term` in the `[zterm]` section:

```
[api]
email=example@example.com
key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
site=https://realm.zulipchat.com

[zterm]
# Alternative themes are listed in the FAQ
theme=zt_dark
# Autohide defaults to 'no_autohide', but can be set to 'autohide' to hide the left & right panels except when focused.
autohide=autohide
# Footlinks default to 'enabled', but can be set to 'disabled' to hide footlinks.
# disabled won't show any footlinks.
# enabled will show the first 3 per message.
footlinks=disabled
# If you need more flexibility, use maximum-footlinks.
# Maximum footlinks to be shown, defaults to 3, but can be set to any value 0 or greater.
# This option cannot be used with the footlinks option; use one or the other.
maximum-footlinks=3
# Notify defaults to 'disabled', but can be set to 'enabled' to display notifications (see next section).
notify=enabled
# Color depth defaults to 256 colors, but can be set to 1 (for monochrome), 16, or 24bit.
color-depth=256
```

> **NOTE:** Most of these configuration settings may be specified on the command line when `zulip-term` is started; `zulip-term -h` or `zulip-term --help` will give the full list of options.

### Notifications

Note that notifications are not currently supported on WSL; see [#767](https://github.com/zulip/zulip-terminal/issues/767).

#### Linux

The following command installs `notify-send` on Debian based systems, similar
commands can be found for other linux systems as well.
```
sudo apt-get install libnotify-bin
```

#### OSX

No additional package is required to enable notifications in OS X. However to have a notification sound, set the following variable (based on your type of shell). The sound value (here Ping) can be any one of the `.aiff` files found at `/System/Library/Sounds` or `~/Library/Sounds`.

*Bash*
```
echo 'export ZT_NOTIFICATION_SOUND=Ping' >> ~/.bash_profile
source ~/.bash_profile
```
*ZSH*
```
echo 'export ZT_NOTIFICATION_SOUND=Ping' >> ~/.zshenv
source ~/.zshenv
```

### Copy to clipboard

Zulip Terminal allows users to copy certain texts to the clipboard via a Python module, [`Pyperclip`](https://pypi.org/project/pyperclip/). This module makes use of various system packages which may or may not come with the OS.
The "Copy to clipboard" feature is currently only available for copying Stream email, from the [Stream information popup](docs/hotkeys.md#stream-list-actions).

#### Linux

On Linux, this module makes use of `xclip` or `xsel` commands, which should already come with the OS. If none of these commands are installed on your system, then install any ONE using:
```
sudo apt-get install xclip [Recommended]
```
OR
```
sudo apt-get install xsel
```

#### OSX and WSL

No additional package is required to enable copying to clipboard.

## Contributor Guidelines

Zulip Terminal is being built by the awesome [Zulip](https://zulip.com/team) community.

To be a part of it and to contribute to the code, feel free to work on any [issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

For commit structure and style, please review the [Commit Style](#commit-style) section below.

If you are new to `git` (or not!), you may benefit from the [Zulip git guide](http://zulip.readthedocs.io/en/latest/git/index.html).
When contributing, it's important to note that we use a **rebase-oriented workflow**.

A simple [tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/developer-feature-tutorial.md) is available for implementing the `typing` indicator.
Follow it to understand how to implement a new feature for zulip-terminal.

You can of course browse the source on GitHub & in the source tree you download, and check the [source file overview](https://github.com/zulip/zulip-terminal/docs/developer-file-overview.md) for ideas of how files are currently arranged.

### Urwid

Zulip Terminal uses [urwid](http://urwid.org/) to render the UI components in terminal. Urwid is an awesome library through which you can render a decent terminal UI just using python. [Urwid's Tutorial](http://urwid.org/tutorial/index.html) is a great place to start for new contributors.

### Setting up a development environment

Various options are available; we are exploring the benefits of each and would appreciate feedback on which you use or feel works best.

Note that the tools used in each case are typically the same, but are called in different ways.

With any option, you first need to clone the zulip/zulip-terminal repository locally (the following will place the repository in the current directory):
```
$ git clone git@github.com:zulip/zulip-terminal.git
```
The following commands should be run in the repository directory, which can be achieved with `cd zulip-terminal`.

#### Pipenv

1. Install pipenv (see the [recommended installation notes](https://pipenv.readthedocs.io/en/latest/install/#pragmatic-installation-of-pipenv); pipenv can be installed in a virtual environment, if you wish)
```
$ pip3 install --user pipenv
```
2. Initialize the pipenv virtual environment for zulip-term (using the default python 3; use eg. `--python 3.6` to be more specific)

```
$ pipenv --three
```

3. Install zulip-term, with the development requirements

```
$ pipenv install --dev
$ pipenv run pip3 install -e '.[dev]'
```

#### Pip

1. Manually create & activate a virtual environment; any method should work, such as that used in the above simple installation

    1. `python3 -m venv zt_venv` (creates a venv named `zt_venv` in the current directory)
    2. `source zt_venv/bin/activate` (activates the venv; this assumes a bash-like shell)

2. Install zulip-term, with the development requirements
```
$ pip3 install -e '.[dev]'
```

#### make/pip

This is the newest and simplest approach, if you have `make` installed:

1. `make` (sets up an installed virtual environment in `zt_venv` in the current directory)
2. `source zt_venv/bin/activate` (activates the venv; this assumes a bash-like shell)

### Development tasks

Once you have a development environment set up, you might find the following useful, depending upon your type of environment:

| Task | Make & Pip | Pipenv |
|-|-|-|
| Run normally | `zulip-term` | `pipenv run zulip-term` |
| Run in debug mode | `zulip-term -d` | `pipenv run zulip-term -d` |
| Run with profiling | `zulip-term --profile` | `pipenv run zulip-term --profile` |
| Run all linters | `./tools/lint-all` | `pipenv run ./tools/lint-all` |
| Run all tests | `pytest` | `pipenv run pytest` |
| Build test coverage report | `pytest --cov-report html:cov_html --cov=./` | `pipenv run pytest --cov-report html:cov_html --cov=./` |

If using make with pip, running `make` will ensure the development environment is up to date with the specified dependencies, useful after fetching from git and rebasing.

#### Passing linters and automated tests

The linters and automated tests (pytest) are run in CI (GitHub Actions) when
you submit a pull request (PR), and we expect them to pass before code is
merged.
> **NOTE:** Mergeable PRs with multiple commits are expected to pass linting
> and tests at **each commit**, not simply overall

Running these tools locally can speed your development and avoid the need
to repeatedly push your code to GitHub simply to run these checks.
> If you have troubles understanding why the linters or pytest are failing,
> please do push your code to a branch/PR and we can discuss the problems in
> the PR or on chat.zulip.org.

All linters and tests can be run using the commands in the table above.
Individual linters may also be run via scripts in `tools/`.

In addition, if using a `make`-based system:
- `make lint` and `make test` run all of each group of tasks
- `make check` runs all checks, which is useful before pushing a PR (or an update)

Correcting some linting errors requires manual intervention, such as from
`mypy` for type-checking.
However, other linting errors may be fixed automatically, as detailed below -
**this can save a lot of time manually adjusting your code to pass the
linters!**

#### Auto-formatting code

The project uses `black` and `isort` for code-style and import sorting respectively.

These tools can be run as linters locally , but can also *automatically* format your code for you.

If you're using a `make`-based setup, running `make fix` will run both (and a
few other tools) and reformat the current state of your code - so you'll want
to commit first just in case, then `--amend` that commit if you're happy with
the changes.

You can also use the tools individually on a file or directory, eg.
`black zulipterminal` or `isort tests/model/test_model.py`

#### Commit Style

We aim to follow a standard commit style to keep the `git log` consistent and easy to read.

Much like working with code, it's great to refer to the git log, for the style we're actively using.

Our overall style for commit structure and messages broadly follows the general [Zulip version control guidelines](http://zulip.readthedocs.io/en/latest/contributing/version-control.html), so we recommend reading that first.

Our commit titles have slight variations from the general Zulip style, with each:
* starting with one or more areas in lower case, followed by a colon and space
* area being slash-separated modified files without extensions, or the type of the change
* ending with a concise description starting with a capital and ending with a full-stop (period)
* having a maximum overall length of 72 (fitting github web interface without abbreviation)

Some example commit titles:
* `file3/file1/file2: Improve behavior of something.` - a general commit updating files `file1.txt`, `file2.py` and `file3.md`
* `refactor: file1/file2: Extract some common function.` - a pure refactor which doesn't change the functional behavior
* `bugfix: file1: Avoid some noticeable bug.` - an ideally small commit to fix a bug
* `tests: file1: Improve test for something.` - only improve tests for `file1`, likely in `test_file1.py`
* `requirements: Upgrade some-dependency from 9.2 to 9.3.` - upgrade a dependency from version 9.2 to version 9.3

Generally with changes to code we request you update linting and tests to pass on a per-commit basis (not just per pull request).
If you update tests, you can add eg. `Tests updated.` in your commit text.

Ideally we prefer that behavioral changes are accompanied by test improvements or additions, and an accompanying `Tests added.` or similar is then useful.

To aid in satisfying some of these rules you can use `GitLint`, as described in the following section.
**However**, please check your commits manually versus these style rules, since GitLint cannot check everything - including language or grammar!

##### GitLint

If you plan to submit git commits in pull-requests (PRs), then we highly suggest installing the `gitlint` commit-message hook by running `gitlint install-hook` (or `pipenv run gitlint install-hook` with pipenv setups). While the content still depends upon your writing skills, this ensures a more consistent formatting structure between commits, including by different authors.

If the hook is installed as described above, then after completing the text for a commit, it will be checked by gitlint against the style we have set up, and will offer advice if there are any issues it notices. If gitlint finds any, it will ask if you wish to commit with the message as it is (`y` for 'yes'), stop the commit process (`n` for 'no'), or edit the commit message (`e` for 'edit').

Other gitlint options are available; for example it is possible to apply it to a range of commits with the `--commits` option, eg. `gitlint --commits HEAD~2..HEAD` would apply it to the last few commits.

### Tips for working with tests (pytest)

Tests for zulip-terminal are written using [pytest](https://pytest.org/). You can read the tests in the `/tests` folder to learn about writing tests for a new class/function. If you are new to pytest, reading its documentation is definitely recommended.

We currently have thousands of tests which get checked upon running `pytest`. While it is dependent on your system capability, this should typically take less than one minute to run. However, during debugging you may still wish to limit the scope of your tests, to improve the turnaround time:
* If lots of tests are failing in a very verbose way, you might try the `-x` option (eg. `pytest -x`) to stop tests after the first failure; due to parametrization of tests and test fixtures, many apparent errors/failures can be resolved with just one fix! (try eg. `pytest --maxfail 3` for a less-strict version of this)
* To avoid running all the successful tests each time, along with the failures, you can run with `--lf` (eg. `pytest --lf`), short for `--last-failed` (similar useful options may be `--failed-first` and `--new-first`, which may work well with `-x`)
* Since pytest 3.10 there is `--sw` (`--stepwise`), which works through known failures in the same way as `--lf` and `-x` can be used, which can be combined with `--stepwise-skip` to control which test is the current focus
* If you know the names of tests which are failing and/or in a specific location, you might limit tests to a particular location (eg. `pytest tests/model`) or use a selected keyword (eg. `pytest -k __handle`)

When only a subset of tests are running it becomes more practical and useful to use the `-v` option (`--verbose`); instead of showing a `.` (or `F`, `E`, `x`, etc) for each test result, it gives the name (with parameters) of each test being run (eg. `pytest -v -k __handle`). This option also shows more detail in tests and can be given multiple times (eg. `pytest -vv`).

For additional help with pytest options see `pytest -h`, or check out the [full pytest documentation](https://docs.pytest.org/en/latest/).

### Debugging Tips

#### Output using `print`

The stdout (standard output) for zulip-terminal is redirected to `./debug.log` if debugging is enabled at run-time using `-d` or `--debug`.

This means that if you want to check the value of a variable, or perhaps indicate reaching a certain point in the code, you can simply use `print()`, eg.
```python3
print(f"Just about to do something with {variable}")
```
and when running with a debugging option, the string will be printed to `./debug.log`.

With a bash-like terminal, you can run something like `tail -f debug.log` in another terminal, to see the output from `print` as it happens.

#### Interactive debugging using pudb & telnet

If you want to debug zulip-terminal while it is running, or in a specific state, you can insert
```python3
from pudb.remote import set_trace
set_trace()
```
in the part of the code you want to debug. This will start a telnet connection for you. You can find the IP address and
port of the telnet connection in `./debug.log`. Then simply run
```
$ telnet 127.0.0.1 6899
```
in another terminal, where `127.0.0.1` is the IP address and `6899` is port you find in `./debug.log`.

#### There's no effect in Zulip Terminal after making local changes!

This likely means that you have installed both normal and development versions of zulip-terminal.

To ensure you run the development version:
* If using pipenv, call `pipenv run zulip-term` from the cloned/downloaded `zulip-terminal` directory;
* If using pip (pip3), ensure you have activated the correct virtual environment (venv); depending on how your shell is configured, the name of the venv may appear in the command prompt. Note that not including the `-e` in the pip3 command will also cause this problem.
