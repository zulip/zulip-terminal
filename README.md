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

  3. Download the zuliprc configuration file to your computer:

  - Log in to the Zulip server(e.g. chat.zulip.org or yourSubdomain.zulipchat.com, or your own development server).
  - Go to _Settings_ -> _Your account_
  - Click on `Show/Change your API key` under the _API key_ section.
  - Download the `zuliprc` file by clicking _Get API key_.
  - Copy the file to a destination of your choice, e.g. to `~/zuliprc`


  4. Run `Zulip-Terminal`
  ```
  ./run.py -c ~/zuliprc
  ```


## Hot Keys
| Command | Key Combination |
| ------- | --------------- |
| Previous message | `Up`, `k` |
| Next message | `Down`, `j` |
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
./run.py -c ~/zuliprc -d
```
* To profile runtime:
```
./run.py -c ~/zuliprc --profile
```
### **Need Help?**
Come meet us at [Zulip](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).
