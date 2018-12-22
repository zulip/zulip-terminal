# Zulip-terminal Changelog

## 0.3.0

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
