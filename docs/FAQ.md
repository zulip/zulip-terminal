# Frequently Asked Questions (FAQ)

## Unable to render non-ASCII characters

**NOTE** Releases of 0.3.2 onwards should not have this issue, or require this solution.

If you see `?` in place of emojis or Zulip Terminal gives a `UnicodeError` / `CanvasError`, you haven't enabled utf-8
encoding in your terminal. To enable it by default, add this to the end of you `~/.bashrc`:

```
export LANG=en_US.utf-8
```

## Unable to open links

If you are unable to open links in messages, then try double right-click on the link.

Alternatively, you might try different modifier keys (eg. shift, ctrl, alt) with a right-click.

If you are still facing problems, please discuss it at
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) or open an issue
for it mentioning your terminal name, version, and OS.

## Mouse does not support *performing some action/feature*

We think of Zulip Terminal as a keyboard-centric client. Consequently, while functionality via the mouse does work in places, mouse support is not currently a priority for the project (see also [#248](https://www.github.com/zulip/zulip-terminal/issues/248)).

## Above mentioned hotkeys don't work as described

If any of the above mentioned hotkeys don't work for you, feel free to open an issue or discuss it on [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

## Zulip-term crashed!

We hope this doesn't happen, but would love to hear about this in order to fix it, since the application should be increasingly stable! Please let us know the problem, and if you're able to duplicate the issue, on the github issue-tracker or at [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

This process would be helped if you could send us the 'traceback' showing the cause of the error, which should be output in such cases:
* version 0.3.1 and earlier: the error is shown on the terminal;
* versions 0.3.2+: the error is present/appended to the file `zulip-terminal-tracebacks.log`.

## Something looks wrong! Where's this feature? There's a bug!
Come meet us on the [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) stream on *chat.zulip.org*.

