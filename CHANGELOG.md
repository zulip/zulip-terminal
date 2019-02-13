# Zulip-terminal Changelog

## Next Release

### Interactivity improvements
- Use <kbd>?</kbd> to show *and* hide help menu (<kbd>esc</kbd> continues to exit)
- Add additional shortcut key for sending messages (<kbd>ctrl</kbd>+<kbd>d</kbd>)
- Allow <kbd>f</kbd> and <kbd>P</kbd> shortcut keys to work from side panels (narrow starred & private messages)
- Warn on startup, if specified theme is lacking current required styles
- Upon unexpected crash, exit cleanly and log traceback to `zulip-terminal-tracebacks.log`

### Visual improvements
- Right-align unread-counts in left & right panels (as in webapp)
- Remove intrusive flashing cursor in side panels
- Truncate text in left & right panels cleanly with '..', avoiding text overflow
- Show user status as `active` (Green), `idle` (Yellow) or `offline` (White) using different colors.
- Further improvement/reordering of shortcut keys in README & help menu (<kbd>?</kbd>)
- Improve styling of help menu, and how the menu scales with application width & height
- Make stream icons bold and correct background color

### Important bugfixes
- Fix bug potentially mixing unread counts for messages from users & streams
- Don't increase the unread counts if we sent the message
- Exit cleanly if cannot connect to zulip server
- Avoid crash in rare case of empty message content
- Set terminal locale to `utf-8` by default which removes issues with rendering double width characters.
- Avoid crash on receiving multiple starred-message events
- Fix quoting original message, not rendered version 

### Infrastructure changes
- Improve installation, development & troubleshooting notes in README
- Minimized initial registration & communication with zulip server
- Internal refactoring & centralization of code handling zulip server communication
- Centralize server event callbacks into Model
- Improve test coverage, including first tests for run.py
- Simplify UI objects used in left & right panels

## 0.3.1

### Interactivity improvements
- Much improved (& configurable on/off) autohide behavior for streams/users panels
- Toggle thumbs-up reactions to messages (<kbd>+</kbd>)
- Toggle star status of messages (<kbd>*</kbd> or <kbd>ctrl</kbd>+<kbd>s</kbd>)
- Narrow to starred messges (<kbd>f</kbd>, or via new button)
- Reply mentioning sender (<kbd>@</kbd>)
- Reply quoting mesage (<kbd>></kbd>)
- Use enter to reply to a message
- Disable responding to suspend (<kbd>ctrl</kbd>+<kbd>z</kbd>), since cannot resume (yet)
- Disable responding to <kbd>ctrl</kbd>+<kbd>s</kbd> for flow control, enabling use with starring

### Visual improvements
- Reorder streams into pinned and unpinned groups
- Style message contents (extracted using beautifulsoup)
- Improve recipient (eg. stream/topic) bar formatting
- Show star status of messages
- Show marker to left of messages
- Mark private streams with P instead of #
- Show unread count of muted streams as M
- Add `gruvbox` theme
- Internal help (<kbd>?</kbd>) more compact & reordered
- Random shortcut keys are shown at the bottom of the screen

### Important bugfixes
- Allow narrowing to cross-realm bots
- Support private messages with multiple users properly
- Avoid showing duplicate recipient bars when scrolling
- Correctly set pointer data (for next unread)
- Improve theme handling on command-line

### Infrastructure changes
- Documentation improvements
- Explicitly support latest versions of python 3.4 to 3.7
- Preliminary support for OSX/Darwin (tested by default)
- Higher test coverage
- Various internal refactoring

## 0.2.1
### Bugfix release

## 0.2.0
### First PyPI release
