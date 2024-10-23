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

`register_initial_desired_events` in `core.py` is the function responsible for registering the events.
``` diff

# zulipterminal/core.py

    @async
    def register_initial_desired_events(self) -> None:
        event_types = [
            'message',
            'update_message',
            # ...
+           'typing',
            # ...
        ]
        response = self.client.register(event_types=event_types,
                                        apply_markdown=True)
```

Now, to see the type of data server is sending we will write the response from the server to a file.

To do so, we temporarily add the following lines to the function `poll_for_events` in `model.py`. The function uses long polling to stay in contact with the server and continuously receives events from the server.

``` diff

# zulipterminal/model.py

            for event in response['events']:
+               with open('type', 'a') as f:
+                   f.write(str(event) + "\n")
                last_event_id = max(last_event_id, int(event['id']))
```

Now, run zulip terminal and open web app from a different account. Start composing a message to your terminal account from the web app and you will start receiving 2 types of events:

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

You can view these events in the `type` file in your `zulip-terminal` home directory.

Now to display if user is typing in the view, we need to check few things:
* The `op` is `start`.
* User is narrowed into direct message conversation with a user.
* The `user_id` of the person is present in the narrowed direct message conversation recipients.

If all the above conditions are satisfied we can successfully update the footer to display `X is typing` until we receive
a `stop` event for typing.

To check for the above conditions, we create a function in `ui.py`:
```python

    def handle_typing_event(self, event: Dict['str', Any]) -> None:
        # If the user is in dm narrow with the person typing
        if len(self.model.narrow) == 1 and\
                self.model.narrow[0][0] == 'pm_with' and\
                event['sender']['email'] in self.model.narrow[0][1].split(','):
            if event['op'] == 'start':
                user = self.model.user_dict[event['sender']['email']]
                self._w.footer.set_text([
                    ' ',
                    ('code', user['full_name']),
                    ' is typing...'
                ])
                self.controller.update_screen()
            elif event['op'] == 'stop':
                self._w.footer.set_text(self.get_random_help())
                self.controller.update_screen()
```
If the conditions are satisfied, we display `x is typing` if the `op` is `start` and display help message if the `op` is `stop`.

There are two parts to updating a widget in urwid:
* Changing the widget
* Updating the screen

This line of code,
```python
self._w.footer.set_text([
                    ' ',
                    ('code', user['full_name']),
                    ' is typing...'
                ])
```
changes the footer text, and this
```python
self.controller.update_screen()
```
updates the screen to display the changes. This fully implements the typing feature.

### Writing tests

Now, we update the tests for `register_initial_desired_events` by adding `typing`
to the event types.
```diff
# tests/core/test_core.py

        event_types = [
            'message',
            'update_message',
            'reaction',
+           'typing',
        ]
        controller.client.register.assert_called_once_with(
                                   event_types=event_types,
                                   apply_markdown=True)
```

`test_handle_typing_event` in `test_ui.py` implements testing for `handle_typing_event`. Please read it to understand how to write tests for a new function in zulip terminal.

Thanks for reading the tutorial. See you on the other side now, i.e, pull request side. :smiley:
