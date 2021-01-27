# Zulip Terminal - [Zulip](https://zulip.com)'s official terminal client

[Recent changes](https://github.com/zulip/zulip-terminal/blob/master/CHANGELOG.md) | [Configuration](#Configuration) | [Hot Keys](#hot-keys) | [FAQs](https://github.com/zulip/zulip-terminal/blob/master/docs/FAQ.md) | [Development](#contributor-guidelines)

[![Zulip chat](https://img.shields.io/badge/zulip-join_chat-brightgreen.svg)](https://chat.zulip.org/#narrow/stream/206-zulip-terminal)
[![PyPI](https://img.shields.io/pypi/v/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![Python Versions](https://img.shields.io/pypi/pyversions/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![GitHub Actions - Linting & tests](https://github.com/zulip/zulip-terminal/workflows/Linting%20%26%20tests/badge.svg?branch=master)](https://github.com/zulip/zulip-terminal/actions?query=workflow%3A%22Linting+%26+tests%22+branch%3Amaster)
[![Coverage status](https://img.shields.io/codecov/c/github/zulip/zulip-terminal/master.svg)](https://app.codecov.io/gh/zulip/zulip-terminal/branch/master)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

![Screenshot](https://user-images.githubusercontent.com/9568999/106061037-b659a580-60a9-11eb-8ff8-ea1c54ac9084.png)

## About

Zulip Terminal is the official terminal client for Zulip, providing a [text-based user interface (TUI)](https://en.wikipedia.org/wiki/Text-based_user_interface).

Specific aims include:
* Providing a broadly similar user experience to the Zulip web client, ultimately supporting all of its features
* Enabling all actions to be achieved through the keyboard (see [Hot keys](#hot-keys))
* Exploring alternative user interface designs suited to the display and input constraints
* Supporting a wide range of platforms and terminal emulators

### Feature status

We consider the client to already provide a fairly stable moderately-featureful everyday-user experience.

The current development focus is on improving aspects of everyday usage which are more commonly used - to reduce the need for users to temporarily switch to another client for a particular feature.

Current limitations which we expect to only resolve over the long term include support for:
* All operations performed by users with extra privileges (owners/admins)
* Accessing and updating all settings
* Using a mouse/pointer to achieve all actions
* An internationalized UI

For queries on missing feature support please take a look at the [Frequently Asked Questions (FAQs)](https://github.com/zulip/zulip-terminal/blob/master/docs/FAQ.md),
our open [Issues](https://github.com/zulip/zulip-terminal/issues/), or sign up on https://chat.zulip.org and chat with users and developers in the [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) stream!

### Supported platforms
- Linux
- OSX
- WSL (On Windows)

### Supported Server Versions

The minimum server version that Zulip Terminal supports is [`2.1.0`](https://zulip.readthedocs.io/en/latest/overview/changelog.html#id7). It may still work with earlier versions.

## Installation

We recommend installing in a dedicated python virtual environment (see below) or using an automated option such as [pipx](https://pypi.python.org/pypi/pipx)

* **Stable** - Numbered stable releases are available on PyPI as the package [zulip-term](https://pypi.python.org/pypi/zulip-term)

  To install, run a command like: `pip3 install zulip-term`

* **Latest** - The latest development version can be installed from the main git repository

  To install, run a command like: `pip3 install git+https://github.com/zulip/zulip-terminal.git@master`

We also provide some sample Dockerfiles to build docker images in [docker/](https://github.com/zulip/zulip-terminal/tree/master/docker).

### Installing into an isolated Python virtual environment

With the python 3.5+ required for running, the following should work on most systems:
1. `python3 -m venv zt_venv` (creates a virtual environment named `zt_venv` in the current directory)
2. `source zt_venv/bin/activate` (activates the virtual environment; this assumes a bash-like shell)
3. Run one of the install commands above, 

If you open a different terminal window (or log-off/restart your computer), you'll need to run **step 2** of the above list again before running `zulip-term`, since that activates that virtual environment. You can read more about virtual environments in the [Python 3 library venv documentation](https://docs.python.org/3/library/venv.html).

## Running for the first time

Upon first running `zulip-term` it looks for a `zuliprc` file, by default in your home directory, which contains the details to log into a Zulip server.

If it doesn't find this file, you have two options:

1. `zulip-term` will prompt you for your server, email and password, and create a `zuliprc` file for you in that location

   **NOTE:** If you use Google, Github or another external authentication to access your Zulip organization then you likely won't have a password set and currently need to create one to use zulip-terminal. If your organization is on Zulip cloud, you can visit https://zulip.com/accounts/go?next=/accounts/password/reset to create a new password for your account. For self-hosted servers please go to your `<Organization URL>/accounts/password/reset/` (eg: https://chat.zulip.org/accounts/password/reset/) to create a new password for your account.

2. Each time you run `zulip-term`, you can specify the path to an alternative `zuliprc` file using the `-c` or `--config-file` options, eg. `$ zulip-term -c /path/to/zuliprc`

   Your personal zuliprc file can be obtained from Zulip servers in your account settings in the web application, which gives you all the permissions you have there. Bot zuliprc files can be downloaded from a similar area for each bot, and will have more limited permissions.

**NOTE:** If your server uses self-signed certificates or an insecure connection, you will need to add extra options to the `zuliprc` file manually - see the documentation for the [Zulip python module](https://pypi.org/project/zulip/).

We suggest running `zulip-term` using the `-e` or `--explore` option (in explore mode) when you are trying Zulip Terminal for the first time, where we intentionally do not mark messages as read.

## Configuration

The `zuliprc` file contains information to connect to your chat server in the `[api]` section, but also optional configuration for `zulip-term` in the `[zterm]` section:

```
[api]
email=example@example.com
key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
site=https://realm.zulipchat.com

[zterm]
# Alternative themes are gruvbox, light and blue
theme=default
# Autohide defaults to 'no_autohide', but can be set to 'autohide' to hide the left & right panels except when focused.
autohide=autohide
# Footlinks default to 'enabled', but can be set to 'disabled' to hide footlinks.
footlinks=disabled
# Notify defaults to 'disabled', but can be set to 'enabled' to display notifications (see next section).
notify=enabled
# Color depth defaults to 256, but can be set to 1 (for monochrome) or 16.
color-depth=256
```

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

## Hot Keys
### General
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Show/hide help menu                                   | <kbd>?</kbd>                                  |
| Show/hide about menu                                  | <kbd>Meta</kbd> + <kbd>?</kbd>                |
| Go back                                               | <kbd>esc</kbd>                                |
| Open draft message saved in this session              | <kbd>d</kbd>                                  |
| Redraw screen                                         | <kbd>Ctrl</kbd> + <kbd>l</kbd>                |
| Quit                                                  | <kbd>Ctrl</kbd> + <kbd>C</kbd>                |

### Navigation
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Previous message                                      | <kbd>Up</kbd> / <kbd>k</kbd>                  |
| Next message                                          | <kbd>Down</kbd> / <kbd>j</kbd>                |
| Go left                                               | <kbd>left</kbd> / <kbd>h</kbd>                |
| Go right                                              | <kbd>right</kbd> / <kbd>l</kbd>               |
| Scroll up                                             | <kbd>PgUp</kbd> / <kbd>K</kbd>                |
| Scroll down                                           | <kbd>PgDn</kbd> / <kbd>J</kbd>                |
| Go to the last message                                | <kbd>G</kbd> / <kbd>end</kbd>                 |
| Narrow to all messages                                | <kbd>a</kbd> / <kbd>esc</kbd>                 |
| Narrow to all private messages                        | <kbd>P</kbd>                                  |
| Narrow to all starred messages                        | <kbd>f</kbd>                                  |
| Narrow to messages in which you're mentioned          | <kbd>#</kbd>                                  |
| Next unread topic                                     | <kbd>n</kbd>                                  |
| Next unread private message                           | <kbd>p</kbd>                                  |

### Searching
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Search users                                          | <kbd>w</kbd>                                  |
| Search messages                                       | <kbd>/</kbd>                                  |
| Search streams                                        | <kbd>q</kbd>                                  |
| Search topics in a stream                             | <kbd>q</kbd>                                  |

### Message actions
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Reply to the current message                          | <kbd>r</kbd>                                  |
| Reply mentioning the sender of the current message    | <kbd>@</kbd>                                  |
| Reply quoting the current message text                | <kbd>></kbd>                                  |
| Reply privately to the sender of the current message  | <kbd>R</kbd>                                  |
| Edit a sent message                                   | <kbd>e</kbd>                                  |
| New message to a stream                               | <kbd>c</kbd>                                  |
| New message to a person or group of people            | <kbd>x</kbd>                                  |
| Narrow to the stream of the current message           | <kbd>s</kbd>                                  |
| Narrow to the topic of the current message            | <kbd>S</kbd>                                  |
| Narrow to a topic/private-chat, or stream/all-private-messages| <kbd>z</kbd>                          |
| Add/remove thumbs-up reaction to the current message  | <kbd>+</kbd>                                  |
| Add/remove star status of the current message         | <kbd>*</kbd>                                  |
| Show/hide message information                         | <kbd>i</kbd>                                  |
| Show/hide edit history (from message information)     | <kbd>e</kbd>                                  |

### Stream list actions
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Toggle topics in a stream                             | <kbd>t</kbd>                                  |
| Mute/unmute Streams                                   | <kbd>m</kbd>                                  |
| Show/hide stream information & modify settings        | <kbd>i</kbd>                                  |
| Show/hide stream members (from stream information)    | <kbd>m</kbd>                                  |

### Composing a message
| Command                                                   | Key Combination                               |
| -----------------------------------------------------     | --------------------------------------------- |
| Cycle through recipient and content boxes                 | <kbd>tab</kbd>                                |
| Send a message                                            | <kbd>Alt Enter</kbd> / <kbd>Ctrl d</kbd>      |
| Save current message as a draft                           | <kbd>Meta</kbd> + <kbd>s</kbd>                |
| Autocomplete @mentions, #stream_names, :emoji: and topics | <kbd>Ctrl</kbd> + <kbd>f</kbd>                |
| Cycle through autocomplete suggestions in reverse         | <kbd>Ctrl</kbd> + <kbd>r</kbd>                |
| Jump to the beginning of line                             | <kbd>Ctrl</kbd> + <kbd>A</kbd>                |
| Jump backward one character                               | <kbd>Ctrl</kbd> + <kbd>B</kbd> / <kbd>←</kbd> |
| Jump backward one word                                    | <kbd>Meta</kbd> + <kbd>B</kbd>                |
| Delete one character                                      | <kbd>Ctrl</kbd> + <kbd>D</kbd>                |
| Delete one word                                           | <kbd>Meta</kbd> + <kbd>D</kbd>                |
| Jump to the end of line                                   | <kbd>Ctrl</kbd> + <kbd>E</kbd>                |
| Jump forward one character                                | <kbd>Ctrl</kbd> + <kbd>F</kbd> / <kbd>→</kbd> |
| Jump forward one word                                     | <kbd>Meta</kbd> + <kbd>F</kbd>                |
| Delete previous character                                 | <kbd>Ctrl</kbd> + <kbd>H</kbd>                |
| Transpose characters                                      | <kbd>Ctrl</kbd> + <kbd>T</kbd>                |
| Kill (cut) forwards to the end of the line                | <kbd>Ctrl</kbd> + <kbd>K</kbd>                |
| Kill (cut) backwards to the start of the line             | <kbd>Ctrl</kbd> + <kbd>U</kbd>                |
| Kill (cut) forwards to the end of the current word        | <kbd>Meta</kbd> + <kbd>D</kbd>                |
| Kill (cut) backwards to the start of the current word     | <kbd>Ctrl</kbd> + <kbd>W</kbd>                |
| Paste last kill                                           | <kbd>Ctrl</kbd> + <kbd>Y</kbd>                |
| Undo last action                                          | <kbd>Ctrl</kbd> + <kbd>_</kbd>                |
| Jump to previous line                                     | <kbd>Ctrl</kbd> + <kbd>P</kbd> / <kbd>↑</kbd> |
| Jump to next line                                         | <kbd>Ctrl</kbd> + <kbd>N</kbd> / <kbd>↓</kbd> |
| Clear compose box                                         | <kbd>Ctrl</kbd> + <kbd>L</kbd>                |


**Note:** You can use `arrows`, `home`, `end`, `Page up` and `Page down` keys to move around in Zulip-Terminal.

## Contributor Guidelines

Zulip Terminal is being built by the awesome [Zulip](https://zulip.com/team) community.

To be a part of it and to contribute to the code, feel free to work on any [issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

Please read our [commit message guidelines](http://zulip.readthedocs.io/en/latest/contributing/version-control.html) and
[git guide](http://zulip.readthedocs.io/en/latest/git/index.html). **NOTE** Due to the difference in project scale, git commit titles in the Zulip Terminal project read slightly differently - please review our recent git log for examples and see the [GitLint](#gitlint) section below for more guidelines.

A simple [tutorial](https://github.com/zulip/zulip-terminal/docs/developer-feature-tutorial.md) is available for implementing the `typing` indicator.
Follow it to understand the how to implement a new feature for zulip-terminal.

You can of course browse the source on GitHub & in the source tree you download, and check the [source file overview](https://github.com/zulip/zulip-terminal/docs/developer-file-overview.md) for ideas of whow files are currently arranged.

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

4. Install mypy manually (mypy is incompatible with pypy, so we don't have this enabled by default)

```
$ pipenv run pip3 install -r requirements.txt
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

NOTE: The linters and pytest are run in CI (GitHub Actions) when you submit a pull request (PR), and we expect them to pass before code is merged. Running them locally can speed your development time, but if you have troubles understanding why the linters or pytest are failing, please do push your code to a branch/PR and we can discuss the problems in the PR or on chat.zulip.org.

If using make with pip, there are corresponding make targets for running linting and testing if you wish to use them (`make lint` & `make test`), and before pushing a pull-request (PR) ready for merging you may find it useful to ensure that `make check` runs successfully (which runs both).

NOTE: The lint script runs a number of separate linters to simplify the development workflow, but each individual linter can be run separately if you find this useful.

#### GitLint

If you plan to submit git commits in pull-requests (PRs), then we highly suggest installing the `gitlint` commit-message hook by running `gitlint install-hook` (or `pipenv run gitlint install-hook` with pipenv setups). While the content still depends upon your writing skills, this ensures a more consistent formatting structure between commits, including by different authors.

If the hook is installed as described above, then after completing the text for a commit, it will be checked by gitlint against the style we have set up, and will offer advice if there are any issues it notices. If gitlint finds any, it will ask if you wish to commit with the message as it is (`y` for 'yes'), stop the commit process (`n` for 'no'), or edit the commit message (`e` for 'edit').

Other gitlint options are available; for example it is possible to apply it to a range of commits with the `--commits` option, eg. `gitlint --commits HEAD~2..HEAD` would apply it to the last few commits.

**NOTE** Not all style suggestions are identified by gitlint at this time, including:
* If modifying code (not just tests), list modified filenames without extensions between slashes in only one area of the commit title (eg. `run/model/core/README: Some description.`)
* If modifying tests in addition to code, just note this in the body of the commit after a blank line (eg. `Tests updated.`)
* If there are multiple areas in the commit title, they are typically used to describe the type of change, which is currently primarily used for a `bugfix`, `refactor` or `tests` (if only modifying tests).
* Updates to dependencies have a `requirements` area only

Generally it is best to refer to the git log to get an idea of the general style to follow, and in particular look for similar types of commits to the ones you are writing.

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

The stdout for zulip-terminal is redirected to `./debug.log` by default.

If you want to check the value of a variable, or perhaps indicate reaching a certain point in the code, you can simply write
```python3
print(variable, flush=True)
```
and the value of the variable will be printed to `./debug.log`.

We suggest the `flush=True` to ensure it prints straight away.

If you have a bash-like terminal, you can run something like `tail -f debug.log` in another terminal, to see the output from `print` as it happens.

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
