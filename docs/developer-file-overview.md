<!--- Generated automatically by tools/lint-docstring.py -->
<!--- Do not modify -->

## Overview

Zulip Terminal uses [Zulip's API](https://zulip.com/api/) to store and retrieve all the information it displays. It has an [MVC structure](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller) overall. Here is a description of some of its files:

| Folder                 | File                | Description                                                                                            |
| ---------------------- | ------------------- | ------------------------------------------------------------------------------------------------------ |
| zulipterminal          | api_types.py        | Types from the Zulip API, translated into python, to improve type checking                             |
|                        | core.py             | Defines the `Controller`, which sets up the `model`, `view`, and coordinates the application           |
|                        | helper.py           | Helper functions used in multiple places                                                               |
|                        | model.py            | Defines the `Model`, fetching and storing data retrieved from the Zulip server                         |
|                        | platform_code.py    | Detection of supported platforms & platform-specific functions                                         |
|                        | server_url.py       | Constructs and encodes server_url of messages.                                                         |
|                        | ui.py               | Defines the `View`, and controls where each component is displayed                                     |
|                        | unicode_emojis.py   | Stores valid unicode emoji data                                                                        |
|                        | urwid_types.py      | Preliminary urwid types to improve type analysis                                                       |
|                        | version.py          | Keeps track of the version of the current code                                                         |
|                        |                     |                                                                                                        |
| zulipterminal/cli      | run.py              | Marks the entry point into the application                                                             |
|                        |                     |                                                                                                        |
| zulipterminal/config   | color.py            | Color definitions or functions common across all themes                                                |
|                        | keys.py             | Keybindings and their helper functions                                                                 |
|                        | markdown_examples.py| Examples of input markdown and corresponding html output (rendered in markdown help)                   |
|                        | regexes.py          | Regular expression constants                                                                           |
|                        | symbols.py          | Terminal characters used to mark particular elements of the user interface                             |
|                        | themes.py           | Styles and their colour mappings in each theme, with helper functions                                  |
|                        | ui_mappings.py      | Relationships between state/API data and presentation in the UI                                        |
|                        | ui_sizes.py         | Fixed sizes of UI elements                                                                             |
|                        |                     |                                                                                                        |
| zulipterminal/ui_tools | boxes.py            | UI boxes for displaying messages and entering text, such as `MessageBox`, `SearchBox`, `WriteBox`, etc.|
|                        | buttons.py          | UI buttons for 'narrowing' and showing unread counts, such as Stream, PM, Topic, Home, Starred, etc    |
|                        | tables.py           | Helper functions which render tables in the UI                                                         |
|                        | utils.py            | The `MessageBox` for every message displayed is created here                                           |
|                        | views.py            | UI views for larger elements such as Streams, Messages, Topics, Help, etc                              |
|                        |                     |                                                                                                        |
| zulipterminal/scripts  |                     | Scripts bundled with the application                                                                   |
|                        |                     |                                                                                                        |
| zulipterminal/themes   |                     | Themes bundled with the application                                                                    |
