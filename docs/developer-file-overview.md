## Overview

Zulip Terminal uses [Zulip's API](https://zulip.com/api/) to store and retrieve all the information it displays. It has an [MVC structure](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller) overall. Here is a description of some of its files:

| Folder                 | File                | Description                                                                                            |
| ---------------------- | ------------------- | ------------------------------------------------------------------------------------------------------ |
| zulipterminal/         | core.py             | Defines the `Controller`, which sets up the `model`, `view`, and coordinates the application           |
|                        | emoji_names.py      | Stores valid emoji names                                                                               |
|                        | helper.py           | Helper functions used in multiple places                                                               |
|                        | model.py            | Defines the `Model`, fetching and storing data retrieved from the Zulip server                         |
|                        | ui.py               | Defines the `View`, and controls where each component is displayed                                     |
|                        | version.py          | Keeps track of the version of the current code                                                         |
|                        |                     |                                                                                                        |
| zulipterminal/cli      | run.py              | Marks the entry point into the application                                                             |
|                        |                     |                                                                                                        |
| zulipterminal/config   | keys.py             | Stores keybindings and their helper functions                                                          |
|                        | themes.py           | Stores styles and their colour mappings in each theme, with helper functions                           |
|                        |                     |                                                                                                        |
| zulipterminal/ui_tools | boxes.py            | UI boxes for displaying messages and entering text, such as `MessageBox`, `SearchBox`, `WriteBox`, etc.|
|                        | buttons.py          | UI buttons for 'narrowing' and showing unread counts, such as Stream, PM, Topic, Home, Starred, etc    |
|                        | tables.py           | Helper functions which render tables in the UI                                                         |
|                        | utils.py            | The `MessageBox` for every message displayed is created here                                           |
|                        | views.py            | UI views for larger elements such as Streams, Messages, Topics, Help, etc                              |
