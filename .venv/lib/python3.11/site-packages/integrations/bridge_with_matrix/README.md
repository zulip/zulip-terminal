# Matrix <--> Zulip bridge

This acts as a bridge between Matrix and Zulip. It also enables a
Zulip topic to be federated between two Zulip servers.

## Usage

### For IRC bridges

Matrix has been bridged to the listed
[IRC networks](https://github.com/matrix-org/matrix-appservice-irc/wiki/Bridged-IRC-networks),
where the 'Room alias format' refers to the `room_id` for the corresponding IRC channel.

For example, for the freenode channel `#zulip-test`, the `room_id` would be
`#freenode_#zulip-test:matrix.org`.

Hence, this can also be used as a IRC <--> Zulip bridge.

## Steps to configure the Matrix bridge

To obtain a configuration file template, run the script with the
`--write-sample-config` option to obtain a configuration file to fill in the
details mentioned below. For example:

* If you installed the `zulip` package: `zulip-matrix-bridge --write-sample-config matrix_bridge.conf`

* If you are running from the Zulip GitHub repo: `python matrix_bridge.py --write-sample-config matrix_bridge.conf`

### 1. Zulip endpoint
1. Create a generic Zulip bot, with a full name like `IRC Bot` or `Matrix Bot`.
2. Subscribe the bot user to the stream you'd like to bridge your IRC or Matrix
   channel into.
3. In the `zulip` section of the configuration file, enter the bot's `zuliprc`
   details (`email`, `api_key`, and `site`).
4. In the same section, also enter the Zulip `stream` and `topic`.

### 2. Matrix endpoint
1. Create a user on [matrix.org](https://matrix.org/), preferably with
   a formal name like to `zulip-bot`.
2. In the `matrix` section of the configuration file, enter the user's username
   and password.
3. Also enter the `host` and `room_id` into the same section.

## Running the bridge

After the steps above have been completed, assuming you have the configuration
in a file called `matrix_bridge.conf`:

* If you installed the `zulip` package: run `zulip-matrix-bridge -c matrix_bridge.conf`

* If you are running from the Zulip GitHub repo: run `python matrix_bridge.py -c matrix_bridge.conf`

## Caveats for IRC mirroring

There are certain
[IRC channels](https://github.com/matrix-org/matrix-appservice-irc/wiki/Channels-from-which-the-IRC-bridge-is-banned)
where the Matrix.org IRC bridge has been banned for technical reasons.
You can't mirror those IRC channels using this integration.
