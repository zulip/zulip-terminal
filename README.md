# Zulip Terminal

An interactive terminal interface for [Zulip](https://zulipchat.com).

 ## Setup:
  1. Download this repository
  ```
  git clone https://github.com/zulip/zulip-terminal
  ```

  2. Install the requirements:
  ```
  cd zulip-terminal
  sudo apt-get install python3-pip
  pip3 install -r requirements.txt
  ```

  3. Download the `zuliprc` file into zulip-terminal directory from [Zulip](https://chat.zulip.org/#settings/your-account)
  under the `API Key` section.

  4. Run `Zulip-Terminal`
  ```
  ./run.py -c ./zuliprc
  ```

## Hot Keys
| Command | Key Combination |
| ------- | --------------- |
| Reply to a message | `r` |
| Reply to an author | `R` |
| New stream message | `c` |
| Move back from Compose box to the message | `esc` |
| Narrow to a stream | `S` |
| Narrow to a topic | `s` |

Note: You can use `arrows`, `home`, `end`, `Page up` and `Page down` keys to move around in Zulip-Terminal.

### Running tests

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
