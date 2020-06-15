# Frequently Asked Questions (FAQ)

## It doesn't seem to run or display properly in my terminal (emulator)?

We have reports of success on the following terminal emulators:

* xterm
* uxterm (see xterm)
* gnome-terminal (https://help.gnome.org/users/gnome-terminal/stable/)
* kitty (https://sw.kovidgoyal.net/kitty/)
* Konsole (KDE) (https://konsole.kde.org/)
* Termite (https://github.com/thestinger/termite)
* Terminator (https://github.com/gnome-terminator/terminator)
* iterm2 (https://iterm2.com/) **Mac only**
* Microsoft/Windows Terminal (https://github.com/Microsoft/Terminal) **Windows only**

Issues have been reported with the following:

* urxvt - **Issues with color rendering**
* mosh (https://mosh.org/) - **Issues with color rendering**
* terminal app **Mac only** - **Issues with some default keypresses, including for sending messages** [zulip-terminal#680](https://github.com/zulip/zulip-terminal/issues/680)

Color issues may be related to the support listed on the urwid page here: http://urwid.org/manual/displayattributes.html#foreground-and-background-settings

Please let us know if you have feedback on the success or failure in these or any other terminal emulator!

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

