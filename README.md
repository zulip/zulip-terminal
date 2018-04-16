# Zulip Terminal

An interactive terminal interface for [Zulip](https://zulipchat.com).

![Build Status](https://travis-ci.org/zulip/zulip-terminal.svg?branch=master)

 ## Setup:
  1. Download this repository
  ```
  git clone https://github.com/zulip/zulip-terminal
  ```

  2. Install the requirements:
  ```
  cd zulip-terminal
  sudo apt-get install python3-pip
  pip3 install pipenv
  pipenv --python 3
  pipenv install
  ```

  3. Download the zuliprc configuration file to your computer:

  - Log in to the Zulip server(e.g. chat.zulip.org or yourSubdomain.zulipchat.com, or your own development server).
  - Go to _Settings_ -> _Your account_
  - Click on `Show/Change your API key` under the _API key_ section.
  - Download the `zuliprc` file by clicking _Get API key_.
  - Copy the file to `~/zuliprc`

  4. Run `Zulip-Terminal`
  ```
  pipenv shell
  ./run.py
  ```
  Alternatively, you can specify the location of `zuliprc` using the -c option
  ```
  ./run.py -c /path/to/zuliprc
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

### Running tests

* Install Dev Requirements:
```
pipenv install --dev
```

* To run all tests:
```
pytest
```

* To generate coverage report for tests:
```
pytest --cov-report html:cov_html --cov=./
```

* To run the linter:
```
pytest --pep8
```

* To check the type annotations, run:
```
./tools/run-mypy
```

* To open in debug mode:
```
./run.py -d
```

* To profile runtime:
```
./run.py --profile
```

### Contributor Guidelines

Zulip Terminal is being build by an awesome community of [Zulip](https://zulipchat.com/team).

To be a part of it and to contribute to the code, feel free to work on any [issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

Do checkout our [commit message guidelines](http://zulip.readthedocs.io/en/latest/contributing/version-control.html) and 
[git guide](http://zulip.readthedocs.io/en/latest/git/index.html).

### **Need Help?**
Come meet us at [Zulip](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).
