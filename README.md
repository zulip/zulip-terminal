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
$ pipsi install 'git+https://github.com/zulip/zulip-terminal.git@master#egg=zulipterminal'
```

3. Download the zuliprc configuration file to your computer:

- Log in to the Zulip server(e.g. chat.zulip.org or yourSubdomain.zulipchat.com, or your own development server).
- Go to _Settings_ -> _Your account_
- Click on `Show/Change your API key` under the _API key_ section.
- Download the `zuliprc` file by clicking _Get API key_.
- Copy the file to `~/zuliprc`

4. Run Zulip Terminal client (`zulip-client`)
```
$ zulip-client
```
Alternatively, you can specify the location of `zuliprc` using the -c option
```
$ zulip-client -c /path/to/zuliprc
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
| Command | Key Combination |
| ------- | --------------- |
| Previous message | `Up`, `k` |
| Next message | `Down`, `j` |
| Go left | `left`, `h` |
| Go right | `right`, `l` |
| Go to the last message | `G`, `end` |
| Narrow to private messages | `P` |
| Scroll down | `PgDn`, `J` |
| Scroll up | `PgUp`, `K` |
| Reply to a message | `r` |
| Reply to an author | `R` |
| New stream message | `c` |
| Move back from Compose box to the message | `esc` |
| Narrow to a stream | `S` |
| Narrow to a topic | `s` |
| Send a message | `Alt Enter` |

Note: You can use `arrows`, `home`, `end`, `Page up` and `Page down` keys to move around in Zulip-Terminal.

## Development

For development, the setup process is a little different.

1. Install pipenv
```
$ curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
$ python3 /tmp/get-pip.py
$ python3 -m pip install --user pipenv
$ printf '\nexport PATH="%s:$PATH"\n' '${HOME}/.local/bin' | tee -a ~/.bashrc
```

2. Clone the zulip/zulip-terminal repository locally
```
$ git clone git@github.com:zulip/zulip-terminal.git
```

3. Install dev requirements
```
$ cd zulip-terminal
$ pipenv --python 3
$ pipenv install --dev
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
pipenv run zulip-client -d
```

* To profile runtime:
```
pipenv run zulip-client --profile
```

### Contributor Guidelines

Zulip Terminal is being build by an awesome community of [Zulip](https://zulipchat.com/team).

To be a part of it and to contribute to the code, feel free to work on any [issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

Do checkout our [commit message guidelines](http://zulip.readthedocs.io/en/latest/contributing/version-control.html) and 
[git guide](http://zulip.readthedocs.io/en/latest/git/index.html).

### **Need Help?**
Come meet us at [Zulip](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).
