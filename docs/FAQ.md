# Frequently Asked Questions (FAQ)

## What Python implementations are supported?

Users and developers run regularly with the "traditional" implementation of
Python (CPython).

We also expect running with [PyPy](https://www.pypy.org) to be smooth based on
our automated testing, though it is worth noting we do not explicitly run the
application in these tests.

Feedback on using these or any other implementations are welcome, such as those
[listed at python.org](https://www.python.org/download/alternatives/).

## What Python versions are supported?

Current practice is to pin minimum and maximum python version support.

As a result:
- the current `main` branch in git supports Python 3.7 to 3.11
- Release 0.7.0 was the last release to support Python 3.6 (maximum 3.10)
- Release 0.6.0 was the last release to support Python 3.5 (maximum 3.9)

Note the minimum versions of Python are close to or in the unsupported range at
this time.

The next release will include support for Python 3.11; before then we suggest
installing the
[latest (git) version](https://github.com/zulip/zulip-terminal/blob/main/README.md#installation).

> Until Mid-April 2023 it is possible that installing with a very recent
> version of Python could lead to an apparently broken installation with a very
> old version of zulip-terminal.
> This should no longer be the case, now that these older versions have been
> yanked from PyPI, but could give symptoms resembling
> [issue 1145](https://github.com/zulip/zulip-terminal/issues/1145).

## What operating systems are supported?

We expect everything to work smoothly on the following operating systems:
* Linux
* macOS
* WSL (Windows Subsystem for Linux)

These are covered in our automatic test suite, though it is assumed that Python
insulates us from excessive variations between distributions and versions,
including when using WSL.

Note that some features are not supported or require extra configuration,
depending on the platform - see
[Configuration](https://github.com/zulip/zulip-terminal/blob/main/README.md#configuration).

> NOTE: Windows is **not** natively supported right now, see
> [#357](https://github.com/zulip/zulip-terminal/issues/357).

`Dockerfile`s have also been contributed, though we don't currently distribute
pre-built versions of these to install - see the [Docker
documentation](https://github.com/zulip/zulip-terminal/blob/main/docker/).

## What versions of Zulip are supported?

For the features that we support, we expect Zulip server versions as far
back as 2.1.0 to be usable.

> NOTE: You can check your server version by pressing
> <kbd>meta</kbd><kbd>?</kbd> in the application.

Note that a subset of features in more recent Zulip versions are supported, and
could in some cases be present when using this client, particularly if the
feature relies upon a client-side implementation.

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

Yes. There are five supported themes:
- `zt_dark` (alias: `default`)
- `gruvbox_dark` (alias: `gruvbox`)
- `gruvbox_light`
- `zt_light` (alias: `light`)
- `zt_blue` (alias: `blue`)

You can specify one of them on the command-line using the command-line option `--theme <theme>` or `-t <theme>` (where _theme_ is the name of the theme, or its alias). You can also specify it in the `zuliprc` file like this:
```
[zterm]
theme=<theme_name>
```
(where _theme_name_ is the name of theme or its alias).

**NOTE** Theme aliases are likely to be deprecated in the future, so we recommend using the full theme names.

## How do links in messages work? What are footlinks?

Each link (hyperlink) in a Zulip message resembles those on the internet, and is split into two parts:
- the representation a user would see on the web page (eg. a textual description)
- the location the link would go to (if clicking, in a GUI web browser)

To avoid squashing these two parts next to each other within the message
content, ZT places only the first within the content, followed by a number in square
brackets, eg. `Zulip homepage [1]`.

Underneath the message content, each location is then listed next to the
related number, eg. `1: zulip.com`. Within ZT we term these **footlinks**,
adapting the idea of a [Footnote](https://wikipedia.org/wiki/Note_(typography))
to show links at the end of a given message.

**NOTE** Footlinks were added in version 0.5.2.

### Why can I only see 3 footlinks when there are more links in my message?

This behavior was introduced in version 0.7.0, to avoid a message with many
links having a very long footlinks list below it.

This can be controlled by giving a different value to the new
`maximum-footlinks` setting in the `zuliprc` file, which defaults to 3.

### Why can I not see the full text of a footlink?

Links can in some cases be long, many multiples of the width of the message
column width. Particularly on narrow terminals, this could cause one link to
take up many lines all by itself as a footlink. Therefore links that wouldn't
fit on one line are clipped in the footlinks, with an ellipsis at the end of
the first line.

**NOTE** If you are able to increase the number of columns of characters - such
as by widening your terminal window or decreasing the font size - you may be
able to see all of the footlink on one line.

### How do I access the full contents of all links, to copy them or open attachments?

To bypass the two practical limitations described in the above sections, the
full contents of every link in a message are available in the **Message
Information** popup, accessible using <kbd>i</kbd> on that message.

The **Message Links** section of this popup contains both the text and location
for each numbered link, using the same numbering system as in the message
content.

The same scrolling keys as used elsewhere in the application can be used in
this popup, and you may notice as you move that different lines of the popup
will be highlighted. If a link is highlighted and you press <kbd>Enter</kbd>,
an action may occur depending on the type of link:
- *Attachments to a particular message* (eg. images, text files, pdfs, etc)
  * will be downloaded, with an option given to open it with your default
    application (from version 0.7.0)
- *Internal links to a stream or topic* (eg. **#announce>terminal releases**,
  from message content such as `#**announce>terminal releases**`)
  * the active narrow will be changed to the stream or topic (from version 0.6.0)
- *External links* (eg. a website, file from a website)
  * no internal action is supported at this time

Any method supported by your terminal emulator to select and copy text should
also be suitable to extract these links. Some emulators can identify links to
open, and may do so in simple cases; however, while the popup is wider than the
message column, it will not fit all lengths of links, and so can fail in the
multiline case (see
[#622](https://www.github.com/zulip/zulip-terminal/issues/622)). Some emulators
may support area selection, as opposed to selecting multiple lines of the
terminal, but it's unclear how common this support is or if it converts such
text into one line suitable for use as a link.

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

## What is autocomplete? Why is it useful?

Autocomplete can be used to request matching options, and cycle through each option in turn, including:
- helping to specify users for new direct messages (eg. after <kbd>x</kbd>)
- helping to specify streams and existing topics for new stream messages (eg. after <kbd>c</kbd>)
- mentioning a user or user-group (in message content)
- linking to a stream or existing topic (in message content)
- emojis (in message content)

This helps ensure that:
- messages are sent to valid users, streams, and matching existing topics if appropriate - so they
  are sent to the correct location;
- message content has references to valid users, user-groups, streams, topics and emojis, with
  correct syntax - so is rendered well in all Zulip clients.

> Note that if using the left or right panels of the application to search for
> streams, topics or users, this is **not** part of the autocomplete system. In
> those cases, as you type, the results of these searches are shown
> automatically by limiting what is displayed in the existing area, until the
> search is cleared. Autocomplete operates differently, and uses the bottom
> line(s) of the screen to show a limited set of matches.

### Hotkeys triggering autocomplete

We use <kbd>ctrl</kbd>+<kbd>**f**</kbd> and <kbd>ctrl</kbd>+<kbd>**r**</kbd> for cycling through autocompletes (**forward** & **reverse** respectively).

**NOTE:** We don't use <kbd>tab</kbd>/<kbd>shift</kbd>+<kbd>tab</kbd> (although it is widely used elsewhere) for cycling through matches. However, recall that we do use <kbd>tab</kbd> to cycle through recipient and content boxes. (See [hotkeys for composing a message](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md#composing-a-message))

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

### Autocomplete of message recipients

Since each of the stream (1), topic (2) and direct message recipients (3) areas are very specific, no prefix must be manually entered and values provided through autocomplete depend upon the context automatically.

![Stream header](https://user-images.githubusercontent.com/55916430/118403323-8e5b7580-b68b-11eb-9c8a-734c2fe6b774.png)

**NOTE:** The stream box prefix is automatic:
* `⊚` (with stream color) if the stream is valid and web-public,
* `#` (with stream color) if the stream is valid and public,
* `P` (with stream color) if the stream is valid and private,
* `✗` if the stream is invalid.

![PM recipients header](https://user-images.githubusercontent.com/55916430/118403345-9d422800-b68b-11eb-9005-6d2af74adab9.png)

**NOTE:** If a direct message recipient's name contains comma(s) (`,`), they are currently treated as comma-separated recipients.

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

