# See zulip_trac.py for installation and configuration instructions

from typing import Optional

# Change these constants to configure the plugin:
ZULIP_USER = "trac-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"
STREAM_FOR_NOTIFICATIONS = "trac"
TRAC_BASE_TICKET_URL = "https://trac.example.com/ticket"

# Most people find that having every change in Trac result in a
# notification is too noisy -- in particular, when someone goes
# through recategorizing a bunch of tickets, that can often be noisy
# and annoying.  We solve this issue by only sending a notification
# for changes to the fields listed below.
#
# TRAC_NOTIFY_FIELDS lets you specify which fields will trigger a
# Zulip notification in response to a trac update; you should change
# this list to match your team's workflow.  The complete list of
# possible fields is:
#
# (priority, milestone, cc, owner, keywords, component, severity,
#  type, versions, description, resolution, summary, comment)
TRAC_NOTIFY_FIELDS = ["description", "summary", "resolution", "comment", "owner"]

## If properly installed, the Zulip API should be in your import
## path, but if not, set a custom path below
ZULIP_API_PATH: Optional[str] = None

# Set this to your Zulip API server URI
ZULIP_SITE = "https://zulip.example.com"
