# Zulip Terminal (zulip-term)

An interactive terminal interface for [Zulip](https://zulip.com).

[Recent changes](https://github.com/zulip/zulip-terminal/blob/master/CHANGELOG.md) | [Configuration](#Configuration) | [Hot Keys](#hot-keys) | [Troubleshooting](#troubleshooting-common-issues) | [Development](#contributor-guidelines)

[![Zulip chat](https://img.shields.io/badge/zulip-join_chat-brightgreen.svg)](https://chat.zulip.org/#narrow/stream/206-zulip-terminal)
[![PyPI](https://img.shields.io/pypi/v/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![Python Versions](https://img.shields.io/pypi/pyversions/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![Build Status](https://travis-ci.org/zulip/zulip-terminal.svg?branch=master)](https://travis-ci.org/zulip/zulip-terminal)
[![Coverage status](https://img.shields.io/codecov/c/github/zulip/zulip-terminal/master.svg)](https://codecov.io/gh/zulip/zulip-terminal)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

![Screenshot 2020-05-19 at 9 56 49 AM](https://user-images.githubusercontent.com/56690786/82285402-0760b800-99b9-11ea-9a86-9d3765ea9177.png)


## Supported platforms
- Linux
- OSX
- WSL (On Windows)

## Installation

We recommend installing in a dedicated python virtual environment (see below) or using an automated option such as [pipx](https://pypi.python.org/pypi/pipx)

* **Stable** - Numbered stable releases are available on PyPI as the package [zulip-term](https://pypi.python.org/pypi/zulip-term)

  To install, run a command like: `pip3 install zulip-term`

* **Latest** - The latest development version can be installed from the main git repository

  To install, run a command like: `pip3 install git+https://github.com/zulip/zulip-terminal.git@master`

We also provide some sample Dockerfiles to build docker images in [docker/](https://github.com/zulip/zulip-terminal/tree/master/docker).

### Installing into an isolated Python virtual environment

With the python 3.5+ required for running, the following should work on most systems:
1. `python3 -m venv zulip-terminal-venv` (creates a venv named `zulip-terminal-venv` in the current directory)
2. `source zulip-terminal-venv/bin/activate` (activates the venv; this assumes a bash-like shell)
3. Run one of the install commands above, 

If you open a different terminal window (or log-off/restart your computer), you'll need to run **step 2** of the above list again before running `zulip-term`, since that activates that virtual environment. You can read more about virtual environments in the [Python 3 library venv documentation](https://docs.python.org/3/library/venv.html).

## Running for the first time

Upon first running `zulip-term` it looks for a `zuliprc` file, by default in your home directory, which contains the details to log into a Zulip server.

If it doesn't find this file, you have two options:

1. `zulip-term` will prompt you for your server, email and password, and create a `zuliprc` file for you in that location

   **NOTE:** If you use Google/Github Auth to login into your zulip organization then you don't have a password and you need to create one. Please go to your `<Your Organization URL>/accounts/password/reset/` (eg: https://chat.zulip.org/accounts/password/reset/) to create a new password for your associated account.

2. Each time you run `zulip-term`, you can specify the path to an alternative `zuliprc` file using the `-c` or `--config-file` options, eg. `$ zulip-term -c /path/to/zuliprc`

   Your personal zuliprc file can be obtained from Zulip servers in your account settings in the web application, which gives you all the permissions you have there. Bot zuliprc files can be downloaded from a similar area for each bot, and will have more limited permissions.

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
# Notify defaults to 'disabled', but can be set to 'enabled' to display notifications (see next section).
notify=enabled
```

### Notifications

#### Linux

The following command installs `notify-send` on Debian based systems, similar
commands can be found for other linux systems as well.
```
sudo apt-get install libnotify-bin
```

#### WSL

Run powershell as **admin** and run these commands to install dependencies for showing notifications:

```
set-executionpolicy remotesigned
Install-Module -Name BurntToast
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
| Go back                                               | <kbd>esc</kbd>                                |
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
| Show message information                              | <kbd>i</kbd>                                  |

### Stream list actions
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Toggle topics in a stream                             | <kbd>t</kbd>                                  |
| Mute/unmute Streams                                   | <kbd>m</kbd>                                  |
| Show stream description                               | <kbd>i</kbd>                                  |

### Composing a message
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Toggle focus box in compose box                       | <kbd>tab</kbd>                                |
| Send a message                                        | <kbd>Alt Enter</kbd> / <kbd>Ctrl d</kbd>      |
| Autocomplete @mentions, #stream_names and :emoji:     | <kbd>Ctrl</kbd> + <kbd>f</kbd>                |
| Cycle through autocomplete suggestions in reverse     | <kbd>Ctrl</kbd> + <kbd>r</kbd>                |
| Jump to the beginning of line                         | <kbd>Ctrl</kbd> + <kbd>A</kbd>                |
| Jump backward one character                           | <kbd>Ctrl</kbd> + <kbd>B</kbd> / <kbd>←</kbd> |
| Jump backward one word                                | <kbd>Meta</kbd> + <kbd>B</kbd>                |
| Delete one character                                  | <kbd>Ctrl</kbd> + <kbd>D</kbd>                |
| Delete one word                                       | <kbd>Meta</kbd> + <kbd>D</kbd>                |
| Jump to the end of line                               | <kbd>Ctrl</kbd> + <kbd>E</kbd>                |
| Jump forward one character                            | <kbd>Ctrl</kbd> + <kbd>F</kbd> / <kbd>→</kbd> |
| Jump forward one word                                 | <kbd>Meta</kbd> + <kbd>F</kbd>                |
| Delete previous character                             | <kbd>Ctrl</kbd> + <kbd>H</kbd>                |
| Transpose characters                                  | <kbd>Ctrl</kbd> + <kbd>T</kbd>                |
| Kill (cut) forwards to the end of the line            | <kbd>Ctrl</kbd> + <kbd>K</kbd>                |
| Kill (cut) backwards to the start of the line         | <kbd>Ctrl</kbd> + <kbd>U</kbd>                |
| Kill (cut) forwards to the end of the current word    | <kbd>Meta</kbd> + <kbd>D</kbd>                |
| Kill (cut) backwards to the start of the current word | <kbd>Ctrl</kbd> + <kbd>W</kbd>                |
| Paste last kill                                       | <kbd>Ctrl</kbd> + <kbd>Y</kbd>                |
| Undo last action                                      | <kbd>Ctrl</kbd> + <kbd>_</kbd>                |
| Jump to previous line                                 | <kbd>Ctrl</kbd> + <kbd>P</kbd> / <kbd>↑</kbd> |
| Jump to next line                                     | <kbd>Ctrl</kbd> + <kbd>N</kbd> / <kbd>↓</kbd> |
| Clear compose box                                     | <kbd>Ctrl</kbd> + <kbd>L</kbd>                |


**Note:** You can use `arrows`, `home`, `end`, `Page up` and `Page down` keys to move around in Zulip-Terminal.

## Troubleshooting: Common issues

### Unable to render non-ASCII characters

**NOTE** Releases of 0.3.2 onwards should not have this issue, or require this solution.

If you see `?` in place of emojis or Zulip Terminal gives a `UnicodeError` / `CanvasError`, you haven't enabled utf-8
encoding in your terminal. To enable it by default, add this to the end of you `~/.bashrc`:

```
export LANG=en_US.utf-8
```

### Unable to open links

If you are unable to open links in messages, then try double right-click on the link.

Alternatively, you might try different modifier keys (eg. shift, ctrl, alt) with a right-click.

If you are still facing problems, please discuss it at
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) or open an issue
for it mentioning your terminal name, version, and OS.

### Mouse does not support *performing some action/feature*

We think of Zulip Terminal as a keyboard-centric client. Consequently, while functionality via the mouse does work in places, mouse support is not currently a priority for the project (see also [#248](https://www.github.com/zulip/zulip-terminal/issues/248)).

### Above mentioned hotkeys don't work as described

If any of the above mentioned hotkeys don't work for you, feel free to open an issue or discuss it on [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

### Zulip-term crashed!

We hope this doesn't happen, but would love to hear about this in order to fix it, since the application should be increasingly stable! Please let us know the problem, and if you're able to duplicate the issue, on the github issue-tracker or at [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

This process would be helped if you could send us the 'traceback' showing the cause of the error, which should be output in such cases:
* version 0.3.1 and earlier: the error is shown on the terminal;
* versions 0.3.2+: the error is present/appended to the file `zulip-terminal-tracebacks.log`.

### Something looks wrong! Where's this feature? There's a bug!
Come meet us on the [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) stream on *chat.zulip.org*.

## Contributor Guidelines

Zulip Terminal is being built by the awesome [Zulip](https://zulip.com/team) community.

To be a part of it and to contribute to the code, feel free to work on any [issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

Please read our [commit message guidelines](http://zulip.readthedocs.io/en/latest/contributing/version-control.html) and
[git guide](http://zulip.readthedocs.io/en/latest/git/index.html).

A simple tutorial for implementing the `typing` indicator is available
in the [wiki](https://github.com/zulip/zulip-terminal/wiki/Developer-Documentation). Follow
it to understand the how to implement a new feature for zulip-terminal.

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
$ pipenv run pip3 install -e .[dev]
```

4. Install mypy manually (mypy is incompatible with pypy, so we don't have this enabled by default)

```
$ pipenv run pip3 install -r requirements.txt
```

#### Pip

1. Manually create & activate a virtual environment; any method should work, such as that used in the above simple installation

    1. `python3 -m venv zulip-terminal-venv` (creates a venv named `zulip-terminal-venv` in the current directory)
    2. `source zulip-terminal-venv/bin/activate` (activates the venv; this assumes a bash-like shell)

2. Install zulip-term, with the development requirements
```
$ pip3 install -e .[dev]
```

### Development tasks

Once you have a development environment set up, you might find the following useful, depending upon your type of environment:

| Task | Pip | Pipenv |
|-|-|-|
| Run normally | `zulip-term` | `pipenv run zulip-term` |
| Run in debug mode | `zulip-term -d` | `pipenv run zulip-term -d` |
| Run with profiling | `zulip-term --profile` | `pipenv run zulip-term --profile` |
| Run all linters | `./tools/lint-all` | `pipenv run ./tools/lint-all` |
| Run all tests | `pytest` | `pipenv run pytest` |
| Build test coverage report | `pytest --cov-report html:cov_html --cov=./` | `pipenv run pytest --cov-report html:cov_html --cov=./` |

NOTE: The linters and pytest are run in CI (travis) when you submit a pull request (PR), and we expect them to pass before code is merged. Running them locally can speed your development time, but if you have troubles understanding why the linters or pytest are failing, please do push your code to a branch/PR and we can discuss the problems in the PR or on chat.zulip.org.

NOTE: The lint script runs a number of separate linters to simplify the development workflow, but each individual linter can be run separately if you find this useful.

#### GitLint (optional)

If you plan to add git commits and submit pull-requests (PRs), then we highly suggest installing the `gitlint` commit-message hook by running `gitlint install-hook` (or `pipenv run gitlint install-hook` with pipenv setups). While the content still depends upon your writing skills, this ensures a more consistent formatting structure between commits, including by different authors.

If the hook is installed as described above, then after completing the text for a commit, it will be checked by gitlint against the style we have set up, and will offer advice if there are any issues it notices. If gitlint finds any, it will ask if you wish to commit with the message as it is (`y` for 'yes'), stop the commit process (`n` for 'no'), or edit the commit message (`e` for 'edit').

Other gitlint options are available; for example it is possible to apply it to a range of commits with the `--commits` option, eg. `gitlint --commits HEAD~2..HEAD` would apply it to the last few commits.

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
