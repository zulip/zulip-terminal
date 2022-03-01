# Frequently Asked Questions (FAQ)

## Colors appear mismatched, don't change with theme, or look strange

Some terminal emulators support specifying custom colors, or custom color schemes. If you do this then this can override the colors that Zulip Terminal attempts to use.

**NOTE** If you have color issues, also note that urwid version 2.1.1 should have fixed these for various terminal emulators (including rxvt, urxvt, mosh and Terminal.app), so please ensure you are running the latest Zulip Terminal release and at least this urwid version before reporting issues.

## It doesn't seem to run or display properly in my terminal (emulator)?

We have reports of success on the following terminal emulators:

* xterm
* uxterm (see xterm)
* rxvt
* urxvt
* gnome-terminal (https://help.gnome.org/users/gnome-terminal/stable/)
* kitty (https://sw.kovidgoyal.net/kitty/)
* Konsole (KDE) (https://konsole.kde.org/)
* Termite (https://github.com/thestinger/termite)
* Terminator (https://github.com/gnome-terminator/terminator)
* iterm2 (https://iterm2.com/) **Mac only**
* mosh (https://mosh.org/)

Issues have been reported with the following:

* (**major**) terminal app **Mac only**
  - Issues with some default keypresses, including for sending messages [zulip-terminal#680](https://github.com/zulip/zulip-terminal/issues/680)
* (**minor**) Microsoft/Windows Terminal (https://github.com/Microsoft/Terminal) **Windows only**
  - Bold text isn't actually bold, it either renders the same as normal text or renders in a different colour [microsoft/terminal#109](https://github.com/microsoft/terminal/issues/109)

Please let us know if you have feedback on the success or failure in these or any other terminal emulator!

## Are there any themes available, other than the default one?

Yes. There are four supported themes:
- `zt_dark` (alias: `default`)
- `gruvbox_dark` (alias: `gruvbox`)
- `zt_light` (alias: `light`)
- `zt_blue` (alias: `blue`)

You can specify one of them on the command-line using the command-line option `--theme <theme>` or `-t <theme>` (where _theme_ is the name of the theme, or its alias). You can also specify it in the `zuliprc` file like this:
```
[zterm]
theme=<theme_name>
```
(where _theme_name_ is the name of theme or its alias).

**NOTE** Theme aliases are likely to be deprecated in the future, so we recommend using the full theme names.

## When are messages marked as having been read?

The approach currently taken is that that a message is marked read when
* it has been selected *or*
* it is a message that you have sent

Unlike the web and mobile apps, we **don't** currently mark as read based on visibility, eg. if you have a message selected and all newer messages are also visible. This makes the marking-read process more explicit, balanced against needing to scroll through messages to mark them. Our styling is intended to promote moving onto unread messages to more easily read them.

In contrast, like with the web app, we don't mark messages as read while in a search - but if you go to a message visible in a search within a topic or stream context then it will be marked as read, just like normal.

An additional feature to other front-ends is **explore mode**, which can be enabled when starting the application (with `-e` or `--explore`); this allows browsing through all your messages and interacting within the application like normal, with the exception that messages are never marked as read. Other than providing a means to test the application with no change in state (ie. *explore* it), this can be useful to scan through your messages quickly when you intend to return to look at them properly later.

## How do I access multiple servers?

One session of Zulip Terminal represents a connection of one user to one Zulip server. Each session refers to a zuliprc file to identify how to connect to the server, so by running Zulip Terminal and specifying a different zuliprc file (using `-c` or `--config-file`), you may connect to a different server. You might choose to do that after exiting from one Zulip Terminal session, or open another terminal and run it concurrently there.

Since we expect the above to be straightforward for most users and it allows the code to remain dramatically simpler, we are unlikely to support multiple Zulip servers within the same session in at least the short/medium term.
However, we are certainly likely to move towards a system to make access of the different servers simpler, which should be made easier through work such as [zulip-terminal#678](https://github.com/zulip/zulip-terminal/issues/678).
In the longer term we may move to multiple servers per session, which is tracked in [zulip-terminal#961](https://github.com/zulip/zulip-terminal/issues/961).

## How do I use autocompletes in ZT?

Composing messages could be a tiring task when you have to type all things by yourself. Autocompletes come to the rescue here! ZT currently supports some basic autocompletes, for different compose boxes.

### Hotkeys triggering autocomplete

We use `ctrl` + **`f`** and `ctrl` + **`r`** for cycling through autocompletes (**forward** & **reverse** respectively).

**NOTE:** We don't use `tab`/`shift tab` (although it is widely used elsewhere) for cycling through matches. However, recall that we do use `tab` to cycle through recipient and content boxes. (See [hotkeys for composing a message](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md#composing-a-message))

### Example: Using autocomplete to add a recognized emoji in your message content

1. Type a prefix designated for an autocomplete (e.g., `:` for autocompleting emojis).
2. Along with the prefix, type the initial letters of the text (e.g., `air` for `airplane`).
3. Now hit the hotkey. You'd see suggestions being listed in the footer (a maximum of 10) if there are any.
4. Cycle between different suggestions as described in above hotkey section. (Notice that a selected suggestion is highlighted)
5. Cycling past the end of suggestions goes back to the prefix you entered (`:air` for this case).

![selected_footer_autocomplete](https://user-images.githubusercontent.com/55916430/116669526-53cfb880-a9bc-11eb-8073-11b220e6f15a.gif)

### Autocomplete in the message content

As in the example above, a specific prefix is required to indicate which action to perform (what text to insert) via the autocomplete:

|Action|Prefix text(s)|Autocompleted text format|
| :--- | :---: | :---: |
|Mention user or user group|`@`|`@*User group*` or `@**User name**`|
|Mention user|`@**`|`@**User name**`|
|Mention user group|`@*`|`@*User group*`|
|Mention user (silently)|`@_`, `@_**`|`@_**User name**`|
|Link to stream|`#`, `#**`|`#**stream name**`|
|Insert emoji|`:`|`:emoji_name:`|

**NOTE:** Currently, the above autocompletes ignore a text containing whitespaces if it is specified as a prefix for autocompletion. (e.g., `#test he` wouldn't lead to `#**test here**`) See also [#925](https://github.com/zulip/zulip-terminal/issues/925).

### Autocomplete of message recipients

Since each of the stream (1), topic (2) and private message recipients (3) areas are very specific, no prefix must be manually entered and values provided through autocomplete depend upon the context automatically.

![Stream header](https://user-images.githubusercontent.com/55916430/118403323-8e5b7580-b68b-11eb-9c8a-734c2fe6b774.png)

**NOTE:** The stream box prefix is automatic:
* `#` (with stream color) if the stream is valid and public,
* `P` (with stream color) if the stream is valid and private,
* `✗` if the stream is invalid.

![PM recipients header](https://user-images.githubusercontent.com/55916430/118403345-9d422800-b68b-11eb-9005-6d2af74adab9.png)

**NOTE:** If a PM recipient's name contains comma(s) (`,`), they are currently treated as comma-separated recipients.

## Unable to render symbols

If some symbols don't render properly on your terminal, it could likely be because of the symbols not being supported on your terminal emulator and/or font.

We provide a tool that you can run with the command `zulip-term-check-symbols` to check whether or not the symbols render properly on your terminal emulator and font configuration.

Ideally, you should see something similar to the following screenshot (taken on the GNOME Terminal) as a result of running the tool:

![Render Symbols Screenshot](https://user-images.githubusercontent.com/60441372/115103315-9a5df580-9f6e-11eb-8c90-3b2585817d08.png)

If you are unable to observe a similar result upon running the tool, please take a screenshot and let us know about it along with your terminal and font configuration by opening an issue or at [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

## Unable to open links

If you are unable to open links in messages, then try double right-click on the link.

Alternatively, you might try different modifier keys (eg. shift, ctrl, alt) with a right-click.

If you are still facing problems, please discuss them at
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) or open issues
for them mentioning your terminal name, version, and OS.

## Links don't render completely as a footlink

Links that don't fit on one line are cropped with an ellipsis in the footlinks, since typically they are not recognized as a link across multiple lines in terminal emulators, copy/pasting can be challenging, and this also saves screen real estate. However, they will become visible with each message if you can widen your terminal window, and they're rendered completely in the Message Information view (see also [#622](https://www.github.com/zulip/zulip-terminal/issues/622)).

**NOTE** Footlinks, ie. footnotes in messages showing the targets of links, exist in release 0.5.2 onwards.

## How small a size of terminal is supported?

While most users likely do not use such sizes, we aim to support sizes from the standard 80 columns by 24 rows upwards.

If you use a width from approximately 100 columns upwards, everything is expected to work as documented.

However, since we currently use a fixed width for the left and right side panels, for widths from approximately 80-100 columns the message list can become too narrow.
In these situations we recommend using the `autohide` option in your configuration file (see [configuration file](https://github.com/zulip/zulip-terminal/#configuration) notes) or on the command-line in a particular session via `--autohide`.

If you use a small terminal size (or simply read long messages), you may find
it useful to read a message which is too long to fit in the window by opening
the Message Information (<kbd>i</kbd>) for a message and scrolling through the Full
rendered message (<kbd>f</kbd>).

If you experience problems related to small sizes that are not resolved using the above, please check [#1005](https://www.github.com/zulip/zulip-terminal/issues/1005)) for any unresolved such issues and report them there.

## Mouse does not support *performing some action/feature*

We think of Zulip Terminal as a keyboard-centric client. Consequently, while functionality via the mouse does work in places, mouse support is not currently a priority for the project (see also [#248](https://www.github.com/zulip/zulip-terminal/issues/248)).

## Hotkeys don't work as described

If any of the hotkeys don't work for you, feel free to open an issue or discuss it on [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

## Zulip-term crashed!

We hope this doesn't happen, but would love to hear about this in order to fix it, since the application should be increasingly stable! Please let us know the problem, and if you're able to duplicate the issue, on the github issue-tracker or at [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

This process would be helped if you could send us the 'traceback' showing the cause of the error, which should be output in such cases:
* version 0.3.1 and earlier: the error is shown on the terminal;
* versions 0.3.2+: the error is present/appended to the file `zulip-terminal-tracebacks.log`.

## Something looks wrong! Where's this feature? There's a bug!
Come meet us on the [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal) stream on *chat.zulip.org*.

