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
