# Developer Feature Tutorial

This tutorial goes through the process of writing a new application feature to Zulip Terminal for first-time contributors.

The process for adding a new feature to Zulip Terminal varies greatly depending on the feature. Hence, this tutorial is intended to make you familiar with the general approach, using an example.

Before diving into this, we recommend you go through Zulip's brilliant [Git Guide](https://zulip.readthedocs.io/en/latest/git/index.html), as we follow a **rebase-oriented workflow**, and our [Commit Discipline Guide](https://zulip.readthedocs.io/en/latest/contributing/version-control.html).

Apart from this, we recommend you also check out the [developer file overview](./developer-file-overview.md) to understand the repository's directory structure.

## Setting up Development Environment

After **forking** and **cloning** the repository, it's time to set up your development environment.

Ideally, we would want to install Zulip Terminal in a **virtual environment** so that your external settings and configurations don't interfere with the development process.

Various ways to do so are listed in the [README](https://github.com/zulip/zulip-terminal#setting-up-a-development-environment) file, but the easiest method is to use `make` if you have it installed.

To install packages and dependencies:

```bash
# To install
$ make
# To enter venv
$ source zt_venv/bin/activate
# To exit venv
$ deactivate
```

**Note**: if you use `pipenv`, you would have to type `pipenv run` before commands to access the virtual environment.

Now, **connect to Zulip upstream** - the main Zulip Terminal repository and make sure your copy is up to date by doing the following:

```bash
$ git fetch upstream

$ git checkout main
Switched to branch 'main'

$ git rebase upstream/main
```

It's best to work in feature branches, so let's create a feature branch from the main branch:

```bash
$ git checkout main
Switched to branch 'main'

$ git checkout -b feature-typing
Switched to a new branch 'feature-typing'
```

You are now ready to contribute!

## Adding Typing Indication

This section shows how the typing indicator was implemented in the terminal client.

Since the typing indicator data for the other user in PM cannot be known without talking to the server, we should establish a connection to the server through Zulip's **REST API**.

We use Zulip API's python bindings instead of making direct HTTP requests. Hence, every API call is made using `zulip.Client()` initialized in the `Controller` class.

```python
# In Controller.__init__
self.client = zulip.Client(config_file=config_file, client=client_identifier)
```

Exploring the [API Doc's](https://chat.zulip.org/api/) shows how to reach various endpoints and what response to expect from the server.

A quick google search for `zulip typing indicator` points to https://zulip.readthedocs.io/en/latest/subsystems/typing-indicators.html. This document explains how typing indicator is implemented on the web client and helps understand how typing indicator works internally.

You can find most of the web features documented in [Zulip Subsystem Doc's](https://zulip.readthedocs.io/en/latest/subsystems) and understand how they work internally.

There are two parts to implementing the typing indicator.

* Receive typing event from server.
* Send typing event to the server.

We will be implementing the first part. **Receive typing event from server**:

On startup, the app registers for the events on the server which it is willing to handle.

`_register_desired_events` in `model.py` is the function responsible for registering events, but the events to be handled are added into a dictionary when `Model` is initialized.

To receive updates for `typing` events, we need to add 'typing' to this dictionary in `Model.__init__`.

```python
# zulipterminal/model.py
# In Model.__init__
self.event_actions: 'OrderedDict[str, Callable[[Event], None]]' = (
    OrderedDict([
        ('message', self._handle_message_event),
        ('update_message', self._handle_update_message_event),
        ('reaction', self._handle_reaction_event),
        ('subscription', self._handle_subscription_event),
>>>     ('typing', self._handle_typing_event),
        ('update_message_flags', self._handle_update_message_flags_event),
        ('update_display_settings', self._handle_update_display_settings_event),
    ])
)
```

As you can see, the second element in the tuple is a Callable. Hence, `_handle_typing_event()` is called whenever a typing response is received. This is the function we will write.

Now, to see the type of data the server is sending, we will write the server's response to a file.

To do so, we temporarily add the following lines to the function `poll_for_events` in `model.py`. The function uses long polling to stay in contact with the server and continuously receives events from the server.

``` python
# zulipterminal/model.py
# In poll_for_events()
    for event in response['events']:
>>>     with open('type_test.json', 'a') as f:
>>>         f.write(str(event) + "\n")
        last_event_id = max(last_event_id, int(event['id']))
```

Now, run Zulip Terminal and open the web app _(or any other client)_ from a different account. Start composing a message to your terminal account from the web app, and you will start receiving two types of events:

**Start:**

```yaml
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

```yaml
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

You can view these events in the `type_test.json` file in your `zulip-terminal` home directory.

Now to display if a user is typing in the View, we need to check few things:

* The `op` is `start`.
* User is narrowed into PM with a user.
* The `user_id` of the sender is present in the PM narrow of the user.

If all the above conditions are satisfied, we can successfully update the footer to display `<sender> is typing...` until we receive a `stop` event for typing.

To check for the above conditions, we create a method in the Model class in `model.py`:

```python
# zulipterminal/model.py
# In Model class
def _handle_typing_event(self, event: Event) -> None:
    """
    Handle typing notifications (in private messages)
    """
    assert event['type'] == "typing"
    if hasattr(self.controller, 'view'):
        # If the user is in pm narrow with the person typing
        narrow = self.narrow
        if (len(narrow) == 1 and narrow[0][0] == 'pm_with' and event['sender']['email'] in narrow[0][1].split(',')):
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

The above code uses the`set_footer_text()` method implemented in the `View` class in `ui.py`, which should default to setting a random Help message when not being used.

If the conditions are satisfied, we display `<sender> is typing...` if the `op` is `start` and display a help message if the `op` is `stop`.

There are two parts to updating a widget in urwid:

* Changing the widget, which is done by View
* Updating the screen, which is done by Controller

These are done by the highlighted lines accordingly in `set_footer_text`

```python
@asynch
def set_footer_text(self, text_list: Optional[List[Any]]=None, duration: Optional[float]=None) -> None:
    if text_list is None:
        text = self.get_random_help()
    else:
        text = text_list
>>> self._w.footer.set_text(text)
>>> self.controller.update_screen()
    if duration is not None:
        assert duration > 0
        time.sleep(duration)
        self.set_footer_text()
```

## Writing tests

We use `pytest` to write all our tests. We have to write new tests, modify current ones or delete old ones whenever needed.

For this feature, we update the tests for `register_initial_desired_events` by adding `typing`
to the event types.

```python
# tests/core/test_core.py
  event_types = [
      'message',
      'update_message',
      'reaction',
      'subscription',
>>>   'typing',
      'update_message_flags',
      'update_display_settings',
  ]
```

and we create a new function `test_handle_typing_event` in `test_model.py` which implements testing for `handle_typing_event`.

Please read it to understand how to write tests for a new function in Zulip Terminal.

How to run these tests? Easy:

* To run all tests, just type `pytest` in your terminal.
* To run linting type `./tools/lint-all` in your terminal.

**Note**: If you happen to be using `pipenv`, use `pipenv run pytest` and `pipenv run ./tools/lint-all` instead.

## Send Pull Request

Remember to delete the modification in `poll_for_events()` and delete the file `type_test.json` before you are ready to commit.

* Use `git status` to check your branch and files changed.
* `git diff` to verify changes.
* `git add` to stage changes.
* `git commit` according to the **commit guidelines**.
* `git rebase -i` Rebase in interactive mode to clean up your commit. _(Lookup squashing)_
* Finally, `git push origin feature-typing` to push to your fork in GitHub.

Now you can go to GitHub and create a **pull request** from the **feature branch** to the main Zulip Terminal repository to be reviewed.

Do send in **[WIP]** PR's or Work In Progress PR's regularly so that we can keep track of your work and advice when needed.

Thanks for reading the tutorial. See you on the other side now, i.e., the pull request side. :smiley:
