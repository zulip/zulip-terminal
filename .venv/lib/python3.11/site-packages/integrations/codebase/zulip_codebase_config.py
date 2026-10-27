from typing import Optional

# Change these values to configure authentication for your codebase account
# Note that this is the Codebase API Username, found in the Settings page
# for your account
CODEBASE_API_USERNAME = "foo@example.com"
CODEBASE_API_KEY = "1234561234567abcdef"

# The URL of your codebase setup
CODEBASE_ROOT_URL = "https://YOUR_COMPANY.codebasehq.com"

# When initially started, how many hours of messages to include.
# Note that the Codebase API only returns the 20 latest events,
# if you have more than 20 events that fit within this window,
# earlier ones may be lost
CODEBASE_INITIAL_HISTORY_HOURS = 12

# Change these values to configure Zulip authentication for the plugin
ZULIP_USER = "codebase-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"

# The streams to send commit information and ticket information to
ZULIP_COMMITS_STREAM_NAME = "codebase"
ZULIP_TICKETS_STREAM_NAME = "tickets"

# If properly installed, the Zulip API should be in your import
# path, but if not, set a custom path below
ZULIP_API_PATH: Optional[str] = None

# Set this to your Zulip API server URI
ZULIP_SITE = "https://zulip.example.com"

# If you wish to log to a file rather than stdout/stderr,
# please fill this out your desired path
LOG_FILE: Optional[str] = None

# This file is used to resume this mirror in case the script shuts down.
# It is required and needs to be writeable.
RESUME_FILE = "/var/tmp/zulip_codebase.state"
