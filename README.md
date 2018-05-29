# Zulip Terminal

An interactive terminal interface for [Zulip](https://zulipchat.com).

![Build Status](https://travis-ci.org/zulip/zulip-terminal.svg?branch=master)  [![Zulip chat](https://img.shields.io/badge/zulip-join_chat-brightgreen.svg)](https://chat.zulip.org/#narrow/stream/206-zulip-terminal)

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

3. Download the zuliprc configuration file to your computer:

- Log in to the Zulip server(e.g. chat.zulip.org or yourSubdomain.zulipchat.com, or your own development server).
- Go to _Settings_ -> _Your account_
- Click on `Show/Change your API key` under the _API key_ section.
- Download the `zuliprc` file by clicking _Get API key_.
- Copy the file to `~/zuliprc`

4. Run Zulip Terminal client (`zulip-term`)
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
| Go Back                                               | <kbd>esc</kbd>                                |
| Narrow to a stream                                    | <kbd>S</kbd>                                  |
| Narrow to a topic                                     | <kbd>s</kbd>                                  |
| Next Unread Topic                                     | <kbd>n</kbd>                                  |
| Next Unread PM                                        | <kbd>p</kbd>                                  |
| Send a message                                        | <kbd>Alt Enter</kbd>                          |
| Search People                                         | <kbd>w</kbd>>                                 |
| Search Messages                                       | <kbd>/</kbd>                                  |
| Beginning of line                                     | <kbd>Ctrl</kbd> + <kbd>A</kbd>                |
| Backward one character                                | <kbd>Ctrl</kbd> + <kbd>B</kbd> / <kbd>←</kbd> |
| Backward one word                                     | <kbd>Meta</kbd> + <kbd>B</kbd>                |
| Delete one character                                  | <kbd>Ctrl</kbd> + <kbd>D</kbd>                |
| Delete one word                                       | <kbd>Meta</kbd> + <kbd>D</kbd>                |
| End of line                                           | <kbd>Ctrl</kbd> + <kbd>E</kbd>                |
| Forward one character                                 | <kbd>Ctrl</kbd> + <kbd>F</kbd> / <kbd>→</kbd> |
| Forward one word                                      | <kbd>Meta</kbd> + <kbd>F</kbd>                |
| Delete previous character                             | <kbd>Ctrl</kbd> + <kbd>H</kbd>                |
| Transpose characters                                  | <kbd>Ctrl</kbd> + <kbd>T</kbd>                |
| Kill (cut) forwards to the end of the line            | <kbd>Ctrl</kbd> + <kbd>K</kbd>                |
| Kill (cut) backwards to the start of the line         | <kbd>Ctrl</kbd> + <kbd>U</kbd>                |
| Kill (cut) forwards to the end of the current word    | <kbd>Meta</kbd> + <kbd>D</kbd>                |
| Kill (cut) backwards to the start of the current word | <kbd>Ctrl</kbd> + <kbd>W</kbd>                |
| Previous line                                         | <kbd>Ctrl</kbd> + <kbd>P</kbd> / <kbd>↑</kbd> |
| Next line                                             | <kbd>Ctrl</kbd> + <kbd>N</kbd> / <kbd>↓</kbd> |
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

### **Need Help?**
Come meet us at [Zulip](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).
