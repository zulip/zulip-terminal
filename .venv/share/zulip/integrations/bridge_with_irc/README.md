# IRC <--> Zulip bridge

## Usage

```
./irc-mirror.py --irc-server=IRC_SERVER --channel=<CHANNEL> --nick-prefix=<NICK> --stream=<STREAM> [optional args]
```

`--stream` is a Zulip stream.  
`--topic` is a Zulip topic, is optionally specified, defaults to "IRC".  
`--nickserv-pw` is the IRC nick password.

IMPORTANT: Make sure the bot is subscribed to the relevant Zulip stream!!

Specify your Zulip API credentials and server in a ~/.zuliprc file or using the options.

IMPORTANT: Note that "_zulip" will be automatically appended to the IRC nick provided, so make sure that your actual registered nick ends with "_zulip".

## Example

```
./irc-mirror.py --irc-server=irc.freenode.net --channel='#python-mypy' --nick-prefix=irc_mirror \
--stream='test here' --topic='#mypy' \
--site="https://chat.zulip.org" --user=<bot-email> \
--api-key=<bot-api-key>
```
