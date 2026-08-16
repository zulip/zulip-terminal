#
from typing import Dict, Optional

# Name of the stream to send notifications to, default is "commits"
STREAM_NAME = "commits"

# Change these values to configure authentication for the plugin
ZULIP_USER = "git-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"

# commit_notice_destination() lets you customize where commit notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * repo   = the name of the git repository
# * branch = the name of the branch that was pushed to
# * commit = the commit id
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit pushed to "main" to
# * stream "commits"
# * topic "main"
# And similarly for branch "test-post-receive" (for use when testing).
def commit_notice_destination(repo: str, branch: str, commit: str) -> Optional[Dict[str, str]]:
    if branch in ["main", "master", "test-post-receive"]:
        return dict(stream=STREAM_NAME, subject=f"{branch}")

    # Return None for cases where you don't want a notice sent
    return None


# Modify this function to change how commits are displayed; the most
# common customization is to include a link to the commit in your
# graphical repository viewer, e.g.
#
# return '!avatar(%s) [%s](https://example.com/commits/%s)\n' % (author, subject, commit_id)
def format_commit_message(author: str, subject: str, commit_id: str) -> str:
    return f"!avatar({author}) {subject}\n"


## If properly installed, the Zulip API should be in your import
## path, but if not, set a custom path below
ZULIP_API_PATH: Optional[str] = None

# Set this to your Zulip server's API URI
ZULIP_SITE = "https://zulip.example.com"
