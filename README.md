# Zulip Terminal - [Zulip](https://zulip.com)'s official terminal client

[Recent changes](https://github.com/zulip/zulip-terminal/blob/main/CHANGELOG.md) | [Configuration](#Configuration) | [Hot Keys](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md) | [FAQs](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md) | [Development](#contributor-guidelines) | [Tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/getting-started.md)

[![Chat with us!](https://img.shields.io/badge/Zulip-chat_with_us!-brightgreen.svg)](https://github.com/zulip/zulip-terminal/blob/main/README.md#chat-with-fellow-users--developers)
[![PyPI](https://img.shields.io/pypi/v/zulip-term.svg)](https://pypi.python.org/pypi/zulip-term)
[![Python Versions](https://img.shields.io/pypi/pyversions/zulip-term.svg)](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#what-python-versions-are-supported)
[![Python Implementations](https://img.shields.io/pypi/implementation/zulip-term.svg)](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#what-python-implementations-are-supported)
[![OS Platforms](https://img.shields.io/static/v1?label=OS&message=Linux%20%7C%20WSL%20%7C%20macOS%20%7C%20Docker&color=blueviolet)](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#what-operating-systems-are-supported)

[![GitHub Actions - Linting & tests](https://github.com/zulip/zulip-terminal/workflows/Linting%20%26%20tests/badge.svg?branch=main)](https://github.com/zulip/zulip-terminal/actions?query=workflow%3A%22Linting+%26+tests%22+branch%3Amain)
[![Coverage status](https://img.shields.io/codecov/c/github/zulip/zulip-terminal/main.svg)](https://app.codecov.io/gh/zulip/zulip-terminal/branch/main)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

![Screenshot](https://user-images.githubusercontent.com/9568999/169362381-3c2b19e2-2176-4ad0-bd41-604946432512.png)

## About

Zulip Terminal is the official terminal client for Zulip, providing a
[text-based user interface (TUI)](https://en.wikipedia.org/wiki/Text-based_user_interface).

Specific aims include:
* Providing a broadly similar user experience to the Zulip web client,
  ultimately supporting all of its features
* Enabling all actions to be achieved through the keyboard (see
  [Hot keys](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md))
* Exploring alternative user interface designs suited to the display and input
  constraints
* Supporting a wide range of platforms and terminal emulators
* Making best use of available rows/columns to scale from 80x24 upwards (see
  [Small terminal notes](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#how-small-a-size-of-terminal-is-supported))

Learn how to use Zulip Terminal with our
[Tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/getting-started.md).

### Feature status

We consider the client to already provide a fairly stable moderately-featureful
everyday-user experience.

The current development focus is on improving aspects of everyday usage which
are more commonly used - to reduce the need for users to temporarily switch to
another client for a particular feature.

Current limitations which we expect to only resolve over the long term include support for:
* All operations performed by users with extra privileges (owners/admins)
* Accessing and updating all settings
* Using a mouse/pointer to achieve all actions
* An internationalized UI

#### Intentional differences

The terminal client currently has a number of intentional differences to the Zulip web client:
- Additional and occasionally *different*
  [Hot keys](https://github.com/zulip/zulip-terminal/blob/main/docs/hotkeys.md)
  to better support keyboard-only navigation; other than directional movement
  these also include:
  - <kbd>z</kbd> - zoom in/out, between streams & topics, or all direct messages & specific conversations
  - <kbd>t</kbd> - toggle view of topics for a stream in left panel
    (**later adopted for recent topics in web client**)
  - <kbd>#</kbd> - narrow to messages in which you're mentioned (<kbd>@</kbd> is already used)
  - <kbd>f</kbd> - narrow to messages you've starred (are **f**ollowing)
- Not marking additional messages read when the end of a conversation is
  visible
  ([FAQ entry](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md#when-are-messages-marked-as-having-been-read))
- Emoji and reactions are rendered as text only, for maximum terminal/font
  compatibility
- Footlinks - footnotes for links (URLs) - make messages readable, while
  retaining a list of links to cross-reference
- Content previewable in the web client, such as images, are also stored as
  footlinks

#### Feature queries?

For queries on missing feature support please take a look at the
[Frequently Asked Questions (FAQs)](https://github.com/zulip/zulip-terminal/blob/main/docs/FAQ.md),
our open [Issues](https://github.com/zulip/zulip-terminal/issues/), or
[chat with users & developers](#chat-with-fellow-users--developers) online at
the Zulip Community server!

## Installation

We recommend installing in a dedicated python virtual environment (see below)
or using an automated option such as [pipx](https://pypi.python.org/pypi/pipx)

* **Stable releases** - These are available on PyPI as the package
  [zulip-term](https://pypi.python.org/pypi/zulip-term)

  To install, run a command like: `pip3 install zulip-term`

* **Latest (git) versions** - The latest development version can be installed
  from the git repository `main` branch

  To install, run a command like:
  `pip3 install git+https://github.com/zulip/zulip-terminal.git@main`

We also provide some sample Dockerfiles to build docker images in
[docker/](https://github.com/zulip/zulip-terminal/tree/main/docker).

### Installing into an isolated Python virtual environment

With the python 3.6+ required for running, the following should work on most
systems:
1. `python3 -m venv zt_venv`
   (creates a virtual environment named `zt_venv` in the current directory)
2. `source zt_venv/bin/activate`
   (activates the virtual environment; this assumes a bash-like shell)
3. Run one of the install commands above, 

If you open a different terminal window (or log-off/restart your computer),
you'll need to run **step 2** of the above list again before running
`zulip-term`, since that activates that virtual environment.
You can read more about virtual environments in the
[Python 3 library venv documentation](https://docs.python.org/3/library/venv.html).

### Keeping your install up to date

Note that there is no automatic-update system, so please track the update
locations relevant to your installation version:

**Stable releases**

Before upgrading, we recommend you check the
[Changes in recent releases](https://github.com/zulip/zulip-terminal/blob/main/CHANGELOG.md)
so you are aware of any important changes between releases.

- These are now announced in the
[#**announce>terminal releases**](https://chat.zulip.org/#narrow/stream/1-announce/topic/terminal.20releases)
topic on the Zulip Community server (https://chat.zulip.org), which is visible
without an account.

  If you wish to receive emails when updates are announced, you are welcome to
sign up for an account on this server, which will enable you to enable email
notifications for the **#announce** stream
([help article](https://zulip.com/help/using-zulip-via-email),
[notifications settings on chat.zulip.org](https://chat.zulip.org/#settings/notifications)).

- You can also customize your GitHub Watch setting on the project page to include releases.

- PyPI provides a
[RSS Release feed](https://pypi.org/rss/project/zulip-term/releases.xml), and
various other services track this information.

**Latest (git) versions**

Versions installed from the `main` git branch will also not update
automatically - the 'latest' refers to the status at the point of installation.

This also applies to other source or development installs
(eg. https://aur.archlinux.org/packages/python-zulip-term-git/).

Therefore, upgrade your package using the command above, or one pertinent to
your package system (eg. Arch).

While the `main` branch is intended to remain stable, if upgrading between two
arbitrary 'latest' versions, please be aware that **changes are not summarized**,
though our commit log should be very readable.

## Running for the first time

Upon first running `zulip-term` it looks for a `zuliprc` file, by default in
your home directory, which contains the details to log into a Zulip server.

If it doesn't find this file, you have two options:

1. `zulip-term` will prompt you for your server, email and password, and create
   a `zuliprc` file for you in that location

   **NOTE:** If you use Google, Github or another external authentication to
   access your Zulip organization then you likely won't have a password set and
   currently need to create one to use zulip-terminal.
   - If your organization is on Zulip cloud, you can visit
   https://zulip.com/accounts/go?next=/accounts/password/reset to create a new
   password for your account.
   - For self-hosted servers please go to your equivalent of
   `<Zulip server URL>/accounts/password/reset/` to create a new password for
   your account (eg: https://chat.zulip.org/accounts/password/reset/).

2. Each time you run `zulip-term`, you can specify the path to an alternative
   `zuliprc` file using the `-c` or `--config-file` options, eg. `$ zulip-term -c
   /path/to/zuliprc`

   A `.zuliprc` file corresponding to your account on a particular Zulip server
   can be downloaded via Web or Desktop applications connected to that server.
   In recent versions this can be found in your **Personal settings** in the
   **Account & privacy** section, under **API key** as 'Show/change your API key'.

   If this is your only Zulip account, you may want to move and rename this
   file to the default file location above, or rename it to something more
   memorable that you can pass to the `---config-file` option.
   **This `.zuliprc` file gives you all the permissions you have as that user.**

   Similar `.zuliprc files` can be downloaded from the **Bots** section for any
   bots you have set up, though with correspondingly limited permissions.

**NOTE:** If your server uses self-signed certificates or an insecure
connection, you will need to add extra options to the `zuliprc` file manually -
see the documentation for the [Zulip python module](https://pypi.org/project/zulip/).

We suggest running `zulip-term` using the `-e` or `--explore` option (in
explore mode) when you are trying Zulip Terminal for the first time, where we
intentionally do not mark messages as read. Try following along with our
[Tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/getting-started.md)
to get the hang of things.

## Configuration

The `zuliprc` file contains two sections:
- an `[api]` section with information required to connect to your Zulip server
- a `[zterm]` section with configuration specific to `zulip-term`

A file with only the first section can be auto-generated in some cases by
`zulip-term`, or you can download one from your account on your server (see
above). Parts of the second section can be added and adjusted in stages when
you wish to customize the behavior of `zulip-term`.

The example below, with dummy `[api]` section contents, represents a working
configuration file with all the default compatible `[zterm]` values uncommented
and with accompanying notes:
```
[api]
email=example@example.com
key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
site=https://example.zulipchat.com

[zterm]
## Theme: available themes can be found by running `zulip-term --list-themes`, or in docs/FAQ.md
theme=zt_dark

## Autohide: set to 'autohide' to hide the left & right panels except when they're focused
autohide=no_autohide

## Footlinks: set to 'disabled' to hide footlinks; 'enabled' will show the first 3 per message
## For more flexibility, comment-out this value, and un-comment maximum-footlinks below
footlinks=enabled
## Maximum-footlinks: set to any value 0 or greater, to limit footlinks shown per message
# maximum-footlinks=3

## Notify: set to 'enabled' to display notifications (see elsewhere for configuration notes)
notify=disabled

## Color-depth: set to one of 1 (for monochrome), 16, 256, or 24bit
color-depth=256
```

> **NOTE:** Most of these configuration settings may be specified on the
command line when `zulip-term` is started; `zulip-term -h` or `zulip-term --help`
will give the full list of options.

### Notifications

Note that notifications are not currently supported on WSL; see
[#767](https://github.com/zulip/zulip-terminal/issues/767).

#### Linux

The following command installs `notify-send` on Debian based systems, similar
commands can be found for other linux systems as well.
```
sudo apt-get install libnotify-bin
```

#### OSX

No additional package is required to enable notifications in OS X.
However to have a notification sound, set the following variable (based on your
type of shell).
The sound value (here Ping) can be any one of the `.aiff` files found at
`/System/Library/Sounds` or `~/Library/Sounds`.

*Bash*
```
echo 'export ZT_NOTIFICATION_SOUND=Ping' >> ~/.bash_profile
source ~/.bash_profile
```
*ZSH*
```
echo 'export ZT_NOTIFICATION_SOUND=Ping' >> ~/.zshenv
source ~/.zshenv
```

### Copy to clipboard

Zulip Terminal allows users to copy certain texts to the clipboard via a Python
module, [`Pyperclip`](https://pypi.org/project/pyperclip/).
This module makes use of various system packages which may or may not come with
the OS.
The "Copy to clipboard" feature is currently only available for copying Stream
email, from the [Stream information popup](docs/hotkeys.md#stream-list-actions).

#### Linux

On Linux, this module makes use of `xclip` or `xsel` commands, which should
already come with the OS.
If none of these commands are installed on your system, then install any ONE
using:
```
sudo apt-get install xclip [Recommended]
```
OR
```
sudo apt-get install xsel
```

#### OSX and WSL

No additional package is required to enable copying to clipboard.

## Chat with fellow users & developers!

While Zulip Terminal is designed to work with any Zulip server, the main
contributors are present on the Zulip Community server at
https://chat.zulip.org, with most conversation in the
[**#zulip-terminal** stream](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

You are welcome to view conversations in that stream using the link above, or
sign up for an account and chat with us - whether you are a user or developer!

We aim to keep the Zulip community friendly, welcoming and productive, so if
participating, please respect our
[Community norms](https://zulip.com/development-community/#community-norms).

### Notes more relevant to the **#zulip-terminal** stream

These are a subset of the **Community norms** linked above, which are more
relevant to users of Zulip Terminal: those more likely to be in a text
environment, limited in character rows/columns, and present in this one smaller
stream.

* **Prefer text in [code blocks](https://zulip.com/help/code-blocks), instead of screenshots**

  Zulip Terminal supports downloading images, but there is no guarantee that
  users will be able to view them.

  *Try <kbd>Meta</kbd>+<kbd>m</kbd> to see example content formatting, including code blocks*

* **Prefer [silent mentions](https://zulip.com/help/mention-a-user-or-group#silently-mention-a-user)
  over regular mentions - or avoid mentions entirely**

  With Zulip's topics, the intended recipient can often already be clear.
  Experienced members will be present as their time permits - responding
  to messages when they return - and others may be able to assist before then.

  (Save [regular mentions](https://zulip.com/help/mention-a-user-or-group#mention-a-user-or-group_1)
  for those who you do not expect to be present on a regular basis)

  *Try <kbd>Ctrl</kbd>+<kbd>f</kbd>/<kbd>b</kbd> to cycle through autocompletion in message content, after typing `@_` to specify a silent mention*

* **Prefer trimming [quote and reply](https://zulip.com/help/quote-and-reply)
  text to only the relevant parts of longer messages - or avoid quoting entirely**

  Zulip's topics often make it clear which message you're replying to. Long
  messages can be more difficult to read with limited rows and columns of text,
  but this is worsened if quoting an entire long message with extra content.

  *Try <kbd>></kbd> to quote a selected message, deleting text as normal when composing a message*

* **Prefer a [quick emoji reaction](https://zulip.com/help/emoji-reactions)
to show agreement instead of simple short messages**

  Reactions take up less space, including in Zulip Terminal, particularly
  when multiple users wish to respond with the same sentiment.

  *Try <kbd>+</kbd> to toggle thumbs-up (+1) on a message, or use <kbd>:</kbd> to search for other reactions*

## Contributor Guidelines

Zulip Terminal is being built by the awesome [Zulip](https://zulip.com/team) community.

To be a part of it and to contribute to the code, feel free to work on any
[issue](https://github.com/zulip/zulip-terminal/issues) or propose your idea on
[#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal).

For commit structure and style, please review the [Commit Style](#commit-style)
section below.

If you are new to `git` (or not!), you may benefit from the
[Zulip git guide](http://zulip.readthedocs.io/en/latest/git/index.html).
When contributing, it's important to note that we use a **rebase-oriented
workflow**.

A simple
[tutorial](https://github.com/zulip/zulip-terminal/blob/main/docs/developer-feature-tutorial.md)
is available for implementing the `typing` indicator.
Follow it to understand how to implement a new feature for zulip-terminal.

You can of course browse the source on GitHub & in the source tree you
download, and check the
[source file overview](https://github.com/zulip/zulip-terminal/blob/main/docs/developer-file-overview.md)
for ideas of how files are currently arranged.

### Urwid

Zulip Terminal uses [urwid](http://urwid.org/) to render the UI components in
terminal.
Urwid is an awesome library through which you can render a decent terminal UI
just using python.
[Urwid's Tutorial](http://urwid.org/tutorial/index.html) is a great place to
start for new contributors.

### Getting Zulip Terminal code and connecting it to upstream

First, fork the `zulip/zulip-terminal` repository on GitHub
([see how](https://docs.github.com/en/get-started/quickstart/fork-a-repo))
and then clone your forked repository locally, replacing **YOUR_USERNAME** with
your GitHub username:

```
$ git clone --config pull.rebase git@github.com:YOUR_USERNAME/zulip-terminal.git
```

This should create a new directory for the repository in the current directory,
so enter the repository directory with `cd zulip-terminal` and configure and
fetch the upstream remote repository for your cloned fork of Zulip Terminal:

```
$ git remote add -f upstream https://github.com/zulip/zulip-terminal.git
```

For detailed explanation on the commands used for cloning and setting upstream,
refer to Step 1 of the
[Get Zulip Code](https://zulip.readthedocs.io/en/latest/git/cloning.html)
section of Zulip's Git guide.

### Setting up a development environment

Various options are available; we are exploring the benefits of each and would
appreciate feedback on which you use or feel works best.

Note that the tools used in each case are typically the same, but are called in
different ways.

The following commands should be run in the repository directory, created by a
process similar to that in the previous section.

#### Pipenv

1. Install pipenv
   (see the [recommended installation notes](https://pipenv.readthedocs.io/en/latest/installation);
   pipenv can be installed in a virtual environment, if you wish)
```
$ pip3 install --user pipenv
```
2. Initialize the pipenv virtual environment for zulip-term (using the default
   python 3; use eg. `--python 3.6` to be more specific)

```
$ pipenv --three
```

3. Install zulip-term, with the development requirements

```
$ pipenv install --dev
$ pipenv run pip3 install -e '.[dev]'
```

#### Pip

1. Manually create & activate a virtual environment; any method should work,
   such as that used in the above simple installation

    1. `python3 -m venv zt_venv` (creates a venv named `zt_venv` in the current directory)
    2. `source zt_venv/bin/activate` (activates the venv; this assumes a bash-like shell)

2. Install zulip-term, with the development requirements
```
$ pip3 install -e '.[dev]'
```

#### make/pip

This is the newest and simplest approach, if you have `make` installed:

1. `make` (sets up an installed virtual environment in `zt_venv` in the current directory)
2. `source zt_venv/bin/activate` (activates the venv; this assumes a bash-like shell)

### Development tasks

Once you have a development environment set up, you might find the following useful, depending upon your type of environment:

| Task | Make & Pip | Pipenv |
|-|-|-|
| Run normally | `zulip-term` | `pipenv run zulip-term` |
| Run in debug mode | `zulip-term -d` | `pipenv run zulip-term -d` |
| Run with profiling | `zulip-term --profile` | `pipenv run zulip-term --profile` |
| Run all linters | `./tools/lint-all` | `pipenv run ./tools/lint-all` |
| Run all tests | `pytest` | `pipenv run pytest` |
| Build test coverage report | `pytest --cov-report html:cov_html --cov=./` | `pipenv run pytest --cov-report html:cov_html --cov=./` |

If using make with pip, running `make` will ensure the development environment
is up to date with the specified dependencies, useful after fetching from git
and rebasing.

#### Passing linters and automated tests

The linters and automated tests (pytest) are run in CI (GitHub Actions) when
you submit a pull request (PR), and we expect them to pass before code is
merged.
> **NOTE:** Mergeable PRs with multiple commits are expected to pass linting
> and tests at **each commit**, not simply overall

Running these tools locally can speed your development and avoid the need
to repeatedly push your code to GitHub simply to run these checks.
> If you have troubles understanding why the linters or pytest are failing,
> please do push your code to a branch/PR and we can discuss the problems in
> the PR or on chat.zulip.org.

All linters and tests can be run using the commands in the table above.
Individual linters may also be run via scripts in `tools/`.

In addition, if using a `make`-based system:
- `make lint` and `make test` run all of each group of tasks
- `make check` runs all checks, which is useful before pushing a PR (or an update)

Correcting some linting errors requires manual intervention, such as from
`mypy` for type-checking.
However, other linting errors may be fixed automatically, as detailed below -
**this can save a lot of time manually adjusting your code to pass the
linters!**

#### Updating hotkeys & file docstrings, vs related documentation

If you update these, note that you do not need to update the text in both
places manually to pass linting.

The source of truth is in the source code, so simply update the python file and
run the relevant tool, as detailed below.

Currently we have
* `tools/lint-hotkeys --fix` to regenerate docs/hotkeys.md from config/keys.py
* `tools/lint-docstring --fix` to regenerate docs/developer-file-overview.md from file docstrings

(these tools are also used for the linting process to ensure that these files are synchronzed)

#### Auto-formatting code

The project uses `black` and `isort` for code-style and import sorting respectively.

These tools can be run as linters locally , but can also *automatically* format
your code for you.

If you're using a `make`-based setup, running `make fix` will run both (and a
few other tools) and reformat the current state of your code - so you'll want
to commit first just in case, then `--amend` that commit if you're happy with
the changes.

You can also use the tools individually on a file or directory, eg.
`black zulipterminal` or `isort tests/model/test_model.py`

#### Structuring Commits - speeding up reviews, merging & development

As you work locally, investigating changes to make, it's common to make a
series of small commits to store your progress.
Often this can include commits that fix linting or testing issues in the
previous commit(s).
These are **developmental-style commits** - and almost everyone is likely to
write commits in this style to some degree.

Developmental-style commits store the changes just fine for you right now.
However, when sharing your code, commit messages are a great place to instead
communicate to others what you're changing and why. Tidying the structure can
also make it easier and quicker for a reader to understand changes, and that you
respect their time. One example is that very large single commits can take a
lot of time to review, compared to if they are split up. Another is if you fix
the tests/linting in a commit: which commit (or commits!) does this fix, and if
it's in the same branch/PR, why isn't the original commit just fixed instead?

Therefore, when creating a Pull Request (PR), please consider that your code is
**more likely to be merged, more quickly, if it is easier to read, understand
and review** - and a big part of that is how you structure your changes into
commits, and describe those changes in commit messages.

To be productive and make it easier for your PRs to be reviewed and updated, we
follow an approach taken at
[Zulip](https://zulip.readthedocs.io/en/latest/contributing/commit-discipline.html)
and elsewhere, aiming for PRs to consist of a series of **minimal coherent**
commits:
* **Minimal**:
  Look at each commit. Does it make different kinds of changes to lots of
  files? Are you treating the title of a commit as a list of changes?  Consider
  how to break down a large change into a sequence of smaller changes that you
  can individually easily describe and that can flow after one another.
* **Coherent**:
  Each commit should individually pass all linting and existing automated
  tests, and if you add new behavior, then add or extend the tests to cover it.

Note that keeping to these principles can give other benefits, both before,
during and after reviewing a PR, including:
* Minimal commits can always later be *squashed* (combined) together - splitting commits is more challenging!
* Coherent commits mean nothing should be broken between and after commits
  * If a new commit in your branch breaks the linting/tests, it's likely that commit at fault!
  * This improves the utility of `git bisect` in your branch or on `main`
* These commits are easier to *reorder* in a branch
  * Commits at the start of a branch (or can be moved there), may be merged early to simplify a branch
* Understanding what changes were made and why is easier when reading a git log comprising these commits

We now enforce a limited aspect of the *coherent* nature of commits in a PR in
a job as part of our Continuous Integration (CI), *Ensure isolated PR commits*,
which essentially runs `make check` on each commit in your branch.  You can
replicate this locally before pushing to GitHub using `tools/check-branch`.

While small or proof-of-concept PRs are initially fine to push as they are,
they will likely only be reviewed based on the overall changes. Generally if
individual commits look like they have a developmental style then reviewers are
likely to give less specific feedback, and minimal coherent commits are certain
to be requested before merging.

**Restructuring commands** - Most restructuring relies upon *interactive
rebasing* (eg. `git rebase -i upstream/main`), but consider searching online
for specific actions, as well as searching or asking in **#git help** or
**#learning** on chat.zulip.org.

**Self review** - Another useful approach is to review your own commits both
locally (see [Zulip
suggestions](https://zulip.readthedocs.io/en/latest/git/setup.html#get-a-graphical-client))
and after you push to GitHub. This allows you to inspect and fix anything that
looks out of place, which someone is likely to pick up in their review, helping
your submissions look more polished, as well as again indicating that you
respect reviewers' time.

#### Commit Message Style

We aim to follow a standard commit style to keep the `git log` consistent and
easy to read.

Much like working with code, we suggest you refer to recent commits in the git
log, for examples of the style we're actively using.

Our overall style for commit messages broadly follows the general guidelines
given for
[Zulip Commit messages](http://zulip.readthedocs.io/en/latest/contributing/commit-discipline.html#commit-messages),
so we recommend reading that first.

Our commit titles (summaries) have slight variations from the general Zulip style, with each:
* starting with one or more **areas** - in lower case, followed by a colon and space
  * generally each commit has at least one area of each modified file - without extensions, separated by a `/`
  * generally *don't* include test files in this list (instead `Tests updated` or `Tests added` in the commit text)
  * other common areas include types like `refactor:`, `bugfix:` and `requirements:` (see below)
* ending with a **concise description** starting with a capital and ending with a full-stop (period)
* having a maximum overall length of 72 (fitting the github web interface without abbreviation)

Some example commit titles: (ideally more descriptive in practice!)
* `file3/file1/file2: Improve behavior of something.`
  - a general commit updating files `file1.txt`, `file2.py` and `file3.md`
* `refactor: file1/file2: Extract some common function.`
  - a pure refactor which doesn't change the functional behavior, involving `file1.py` and `file2.py`
* `bugfix: file1: Avoid some noticeable bug.`
  - a small commit to fix a bug in `file1.py`
* `tests: file1: Improve test for something.`
  - only improve tests for `file1`, likely in `test_file1.py`
* `requirements: Upgrade some-dependency from ==9.2 to ==9.3.`
  - upgrade a dependency from version ==9.2 to version ==9.3, in the central dependencies file (*not* some file requirements.*)

To aid in satisfying some of these rules you can use `GitLint`, as described in
the following section.

**However**, please check your commits manually versus these style rules, since
GitLint cannot check everything - including language or grammar!

#### GitLint

If you plan to submit git commits in pull-requests (PRs), then we highly
suggest installing the `gitlint` commit-message hook by running `gitlint
install-hook` (or `pipenv run gitlint install-hook` with pipenv setups).
While the content still depends upon your writing skills, this ensures a more
consistent formatting structure between commits, including by different
authors.

If the hook is installed as described above, then after completing the text for
a commit, it will be checked by gitlint against the style we have set up, and
will offer advice if there are any issues it notices.
If gitlint finds any, it will ask if you wish to commit with the message as it
is (`y` for 'yes'), stop the commit process (`n` for 'no'), or edit the commit
message (`e` for 'edit').

Other gitlint options are available; for example it is possible to apply it to
a range of commits with the `--commits` option, eg. `gitlint --commits
HEAD~2..HEAD` would apply it to the last few commits.

### Tips for working with tests (pytest)

Tests for zulip-terminal are written using [pytest](https://pytest.org/).
You can read the tests in the `/tests` folder to learn about writing tests for
a new class/function.
If you are new to pytest, reading its documentation is definitely recommended.

We currently have thousands of tests which get checked upon running `pytest`.
While it is dependent on your system capability, this should typically take
less than one minute to run.
However, during debugging you may still wish to limit the scope of your tests,
to improve the turnaround time:

* If lots of tests are failing in a very verbose way, you might try the `-x`
  option (eg. `pytest -x`) to stop tests after the first failure; due to
parametrization of tests and test fixtures, many apparent errors/failures can
be resolved with just one fix! (try eg. `pytest --maxfail 3` for a less-strict
version of this)

* To avoid running all the successful tests each time, along with the failures,
  you can run with `--lf` (eg. `pytest --lf`), short for `--last-failed`
(similar useful options may be `--failed-first` and `--new-first`, which may
work well with `-x`)

* Since pytest 3.10 there is `--sw` (`--stepwise`), which works through known
  failures in the same way as `--lf` and `-x` can be used, which can be
combined with `--stepwise-skip` to control which test is the current focus

* If you know the names of tests which are failing and/or in a specific
  location, you might limit tests to a particular location (eg. `pytest
tests/model`) or use a selected keyword (eg. `pytest -k __handle`)

When only a subset of tests are running it becomes more practical and useful to
use the `-v` option (`--verbose`); instead of showing a `.` (or `F`, `E`, `x`,
etc) for each test result, it gives the name (with parameters) of each test
being run (eg. `pytest -v -k __handle`).
This option also shows more detail in tests and can be given multiple times
(eg. `pytest -vv`).

For additional help with pytest options see `pytest -h`, or check out the [full
pytest documentation](https://docs.pytest.org/en/latest/).

### Debugging Tips

#### Output using `print`

The stdout (standard output) for zulip-terminal is redirected to `./debug.log`
if debugging is enabled at run-time using `-d` or `--debug`.

This means that if you want to check the value of a variable, or perhaps
indicate reaching a certain point in the code, you can simply use `print()`,
eg.
```python3
print(f"Just about to do something with {variable}")
```
and when running with a debugging option, the string will be printed to
`./debug.log`.

With a bash-like terminal, you can run something like `tail -f debug.log` in
another terminal, to see the output from `print` as it happens.

#### Interactive debugging using pudb & telnet

If you want to debug zulip-terminal while it is running, or in a specific
state, you can insert
```python3
from pudb.remote import set_trace
set_trace()
```
in the part of the code you want to debug.
This will start a telnet connection for you. You can find the IP address and
port of the telnet connection in `./debug.log`. Then simply run
```
$ telnet 127.0.0.1 6899
```
in another terminal, where `127.0.0.1` is the IP address and `6899` is port you
find in `./debug.log`.

#### There's no effect in Zulip Terminal after making local changes!

This likely means that you have installed both normal and development versions
of zulip-terminal.

To ensure you run the development version:
* If using pipenv, call `pipenv run zulip-term` from the cloned/downloaded
  `zulip-terminal` directory;

* If using pip (pip3), ensure you have activated the correct virtual
  environment (venv); depending on how your shell is configured, the name of
the venv may appear in the command prompt.
Note that not including the `-e` in the pip3 command will also cause this
problem.
