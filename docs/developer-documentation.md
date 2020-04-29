**Zulip Terminal** is a light and fast terminal client for [Zulip](https://zulipchat.com). It's written in python and :snake: only.

## Overview

Zulip Terminal uses [Zulip's API](https://zulipchat.com/api/) to store and retrieve all the information it displays. It has an [MVC structure](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller) overall. Here is a description of some of its files:

| Folder                 | File                | Description                                              |
| ---------------------- | ------------------- | -------------------------------------------------------- |
| zulipterminal/         | core.py             | Sets up the model, view and runs the application         |
|                        | helper.py           | Helper functions used at multiple places                 |
|                        | model.py            | Fetches and stores data retrieved from server            |
|                        | ui.py               | Controls where each component is displayed               |
|                        | version.py          | Keeps track of the latest releases PyPI version          |
|                        |                     |                                                          |
| zulipterminal/cli      | run.py              | Marks the entry point into the application               |
|                        |                     |                                                          |
| zulipterminal/config   | keys.py             | Stores keybindings and their helper functions            |
|                        | themes.py           | Stores different themes and their colour mappings        |
|                        |                     |                                                          |
| zulipterminal/ui_tools | boxes.py            | UI boxes such as WriteBox, MessageBox and SearchBox      |
|                        | buttons.py          | UI buttons such as Stream, PM, Topic, Home, Starred, etc |
|                        | tables.py           | Helper functions which render tables in the UI           |
|                        | utils.py            | MessageBox for every message displayed is created here   |
|                        | views.py            | UI views such as Streams, Messages, Topics, Help, etc    |

Zulip Terminal uses [urwid](http://urwid.org/) to render the UI components in terminal. Urwid is an awesome library through which you can render a decent terminal UI just using python. [Urwid's Tutorial](http://urwid.org/tutorial/index.html) is a great place to start for new contributors.


## Tests

Tests for zulip-terminal are written using [pytest](https://pytest.org/). You can read the tests in `/tests` folder to learn about writing tests for a new class/function. If you are new to pytest, reading its documentation is definitely recommended.


## Tutorial - Adding typing indicator

This tutorial shows how typing indicator was implemented in the client. The process for adding a new feature to zulip terminal varies greatly depending on the feature. This tutorial is intended to make you familiar with the general process.

Since the typing indicator data for the other user in pm cannot be generated locally, it should be received from the client.

A quick google search for `zulip typing indicator` points to https://zulip.readthedocs.io/en/latest/subsystems/typing-indicators.html. This document explains how typing indicator is implemented on the web client and is useful in understanding how typing indicator works internally.

You can find most of the web features documented in https://zulip.readthedocs.io/en/latest/subsystems and understand how they work internally.

https://chat.zulip.org/api/ shows how to reach the endpoints and what response to expect from the server. There are two parts to this feature.

There are two parts to implementing typing indicator.
* Receive typing event from server.
* Send typing event to the server.

We will be implementing the first part. **Receive typing event from server**:

On startup, the app registers for the events on the server which it is willing to handle. To receive updates for `typing` events, we need to add 'typing' to the initially registered events.

The `self.event_actions` in `model.py` is the data structure responsible for containing all the events which we are about to register with the server.
Add the `typing` entry there with the handler function (defined later).

``` diff python
# zulipterminal/model.py

    self.event_actions = OrderedDict([
        # ...
+       ('typing', self._handle_typing_event),
        # ...
    ])  # type: OrderedDict[str, Callable[[Event], None]]
```

This is necessary, as in the `_register_desired_events` in `model.py` we use `self.client.register` to register the desired event. This function is provided to us by the Zulip API. For more details, refer https://zulipchat.com/api/register-queue.

Now, to see the type of data server is sending we will write the response from the server to a file. To do so, we temporarily add the following line to the function `poll_for_events` in `model.py`. The function uses long polling to stay in contact with the server and continuously receive events from the server.

``` diff
# zulipterminal/model.py

            for event in response['events']:
+             print(event, flush=True)
              last_event_id = max(last_event_id, int(event['id']))
```

Now, run zulip terminal and open web app from a different account. Start composing a message to your terminal account (PM) from the web app and you will start receiving 2 types of events:

**Start**
```
{
  'type': 'typing',
  'op': 'start',
  'sender': {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  },
  'recipients': [{
    'user_id': 2,
    'email': 'ZOE@zulip.com'
  }, {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  }, {
    'user_id': 5,
    'email': 'iago@zulip.com'
  }],
  'id': 0
}
```

**Stop**
```
{
  'type': 'typing',
  'op': 'stop',
  'sender': {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  },
  'recipients': [{
    'user_id': 2,
    'email': 'ZOE@zulip.com'
  }, {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  }, {
    'user_id': 5,
    'email': 'iago@zulip.com'
  }],
  'id': 1
}
```

You can view the output of these events in the `debug.log` file in your `zulip-terminal` home directory.

Now to display if user is typing in the view, we need to check few things:
* The `op` is `start`.
* User is narrowed into PM with a user.
* The `user_id` of the person is present in the narrowed PM recipients.

If all the above conditions are satisfied we can successfully update the footer to display `X is typing` until we receive
a `stop` event for typing.

To check for the above conditions, we define the callback, a function in `model.py`:
```python

    def _handle_typing_event(self, event: Event) -> None:
        """
        Handle typing notifications (in private messages)
        """
        if hasattr(self.controller, 'view'):
            # If the user is in pm narrow with the person typing
            if len(self.narrow) == 1 and self.narrow[0][0] == 'pm_with' and\
                    event['sender']['email'] in self.narrow[0][1].split(','):
                if event['op'] == 'start':
                    user = self.user_dict[event['sender']['email']]
                    self.controller.view.set_footer_text([
                        ' ',
                        ('code', user['full_name']),
                        ' is typing...'
                    ])
                elif event['op'] == 'stop':
                    self.controller.view.set_footer_text()
                else:
                    raise RuntimeError("Unknown typing event operation")
```
If the conditions are satisfied, we use the `set_footer_text` defined in `ui.py` to display `x is typing` if the `op` is `start` and display help message if the `op` is `stop`.

There are two parts to updating a widget in urwid:
* Changing the widget
* Updating the screen

This line of code inside `view.set_footer_text`,

```python
self._w.footer.set_text(text)
```

changes the footer text, and this

```python
self.controller.update_screen()
```

updates the screen to display the changes. This fully implements the typing feature.

### Writing tests

Now, we update the tests for `test_register_initial_desired_events` by adding `typing`
to the event types.

```diff
# tests/model/test_model.py

        event_types = [
            # ...
+           'typing',
            # ...
        ]
```

`test__handle_typing_event` in `test_model.py` implements testing for `_handle_typing_event`. Please read it to understand how to write tests for a new function in zulip terminal.

Lastly, in order for our linters to pass (specifically mypy), make sure you add any fields specific to the `typing` event in the event TypedDict.

``` diff
# zulipterminal/model.py

Event = TypedDict('Event', {
    # ...
+   # typing:
+    'sender': Dict[str, Any],  # 'email', ...
+    # typing & reaction:
+    'op': str,
    # ...
```

Thanks for reading the tutorial. See you on the other side now, i.e, pull request side. :smiley: