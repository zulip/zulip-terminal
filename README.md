# Zulip Terminal

An interactive terminal interface for [Zulip](https://zulipchat.com).

![Build Status](https://travis-ci.org/zulip/zulip-terminal.svg?branch=master)  [![Zulip chat](https://img.shields.io/badge/zulip-join_chat-brightgreen.svg)](https://chat.zulip.org/#narrow/stream/206-zulip-terminal)
 [![Coverage status](https://img.shields.io/codecov/c/github/zulip/zulip-terminal/master.svg)](
https://codecov.io/gh/zulip/zulip-terminal)
## Setup:

1. Download and install the prerequisite tools ([pipsi](https://github.com/mitsuhiko/pipsi))
```
$ curl -SsLo /tmp/get-pipsi.py https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py
$ python3 /tmp/get-pipsi.py
$ printf '\nexport PATH="%s:$PATH"\n' '${HOME}/.local/bin' | tee -a ~/.bashrc
```

2. Install the package:
```
$ pipsi install --python python3 'git+https://github.com/zulip/zulip-terminal.git@master#egg=zulipterminal'
```

3. Run Zulip Terminal:
```
$ zulip-term
```
Alternatively, you can specify the location of `zuliprc` using the -c option
```
$ zulip-term -c /path/to/zuliprc
```

## Example zuliprc file
```
[api]
email=example@example.com
key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
site=https://realm.zulipchat.com

[zterm]
# Theme can also be set to 'blue' and 'light'
theme=default
```

## Hot Keys
| Command                                               | Key Combination                               |
| ----------------------------------------------------- | --------------------------------------------- |
| Previous message                                      | <kbd>Up</kbd> / <kbd>k</kbd>                  |
| Next message                                          | <kbd>Down</kbd> / <kbd>j</kbd>                |
| Go left                                               | <kbd>left</kbd> / <kbd>h</kbd>                |
| Go right                                              | <kbd>right</kbd> / <kbd>l</kbd>               |
| Go to the last message                                | <kbd>G</kbd> / <kbd>end</kbd>                 |
| Narrow to private messages                            | <kbd>P</kbd>                                  |
| Scroll down                                           | <kbd>PgDn</kbd> / <kbd>J</kbd>                |
| Scroll up                                             | <kbd>PgUp</kbd> / <kbd>K</kbd>                |
| Reply to a message                                    | <kbd>r</kbd>                                  |
| Reply to an author                                    | <kbd>R</kbd>                                  |
| New stream message                                    | <kbd>c</kbd>                                  |
| New private message                                   | <kbd>x</kbd>                                  |
| Go Back                                               | <kbd>esc</kbd>                                |
| Narrow to a stream                                    | <kbd>S</kbd>                                  |
| Narrow to a topic                                     | <kbd>s</kbd>                                  |
| Next Unread Topic                                     | <kbd>n</kbd>                                  |
| Next Unread PM                                        | <kbd>p</kbd>                                  |
| Send a message                                        | <kbd>Alt Enter</kbd>                          |
| Search People                                         | <kbd>w</kbd>                                  |
| Search Messages                                       | <kbd>/</kbd>                                  |
| Jump to the Beginning of line                         | <kbd>Ctrl</kbd> + <kbd>A</kbd>                |
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
| Clear screen                                          | <kbd>Ctrl</kbd> + <kbd>L</kbd>                |

Note: You can use `arrows`, `home`, `end`, `Page up` and `Page down` keys to move around in Zulip-Terminal.

## Development

For development, the setup process is a little different.

1. Install pipenv
```
$ curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
$ python3 /tmp/get-pip.py --user
$ printf '\nexport PATH="%s:$PATH"\n' '${HOME}/.local/bin' | tee -a ~/.bashrc
$ python3 -m pip install --user pipenv
```

2. Clone the zulip/zulip-terminal repository locally
```
$ git clone git@github.com:zulip/zulip-terminal.git
```

3. Install dev requirements
```
$ cd zulip-terminal
$ pipenv --three
$ pipenv install --dev
$ pipenv run python setup.py develop
```

4. Run the client
```
$ pipenv run zulip-term
```

### Running tests

* To run all tests:
```
pipenv run pytest
```

* To generate coverage report for tests:
```
pipenv run pytest --cov-report html:cov_html --cov=./
```

* To run the linter:
```
pipenv run pytest --pep8
```

* To check the type annotations, run:
```
pipenv run ./tools/run-mypy
```

* To open in debug mode:
```
pipenv run zulip-term -d
```

* To profile runtime:
```
pipenv run zulip-term --profile
```

### Contributor Guidelines

Zulip Terminal is being build by an awesome community of [Zulip](https://zulipchat.com/team).

To be a part of it and to contribute to the code, feel free to work on any [issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

Do checkout our [commit message guidelines](http://zulip.readthedocs.io/en/latest/contributing/version-control.html) and
[git guide](http://zulip.readthedocs.io/en/latest/git/index.html).

### Debugging Tips

The stdout for zulip-terminal is set to `/tmp/debug.log` by default. 
If you want to check the value of a variable, you can simply write
```
print(variable)
```
and the value of the variable will be printed to `/tmp/debug.log`.

If you want to debug zulip-terminal while it is running, or in a specific state, you can insert
```
from pudb.remote import set_trace
set_trace()
```
in the part of the code you want to debug. This will start a telnet connection for you. You can find the IP address and
port of the telnet connection in `/tmp/debug.log`. Then simply run
```
$ telnet 127.0.0.1 6899
```
in another terminal, where `127.0.0.1` is the IP address and `6899` is port you find in `/tmp/debug.log`.

### **Need Help?**
Come meet us at [Zulip](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

Troubleshooting: Common issues
------------------------------

##### Unable to render non-ASCII characters

If you see `?` in place of emojis or Zulip Terminal gives a `UnicodeError` / `CanvasError`, you haven't enabled utf-8
encoding in your terminal. To enable it by default, add this to the end of you `~/.bashrc`:

```
export LANG=en_US.utf-8
```

##### Unable to open links

If you are unable to open links in messages, then try double right-click on the link.
If you are still facing problems, please discuss it at
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) or open an issue
for it mentioning your terminal name, version, and OS.

##### [DEV] No effect on Zulip Terminal on making local changes

This means that you have installed both Normal and development versions of zulip-terminal. For running the development version, call
`pipenv run zulip-term` from the cloned / downloaded `zulip-terminal` directory.

##### Above mentioned hotkeys don't work as described

If any of the above mentioned hotkeys don't work for you, feel free to open an issue or discuss it on [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).
