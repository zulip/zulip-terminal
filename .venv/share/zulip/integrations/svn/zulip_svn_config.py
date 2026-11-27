from typing import Dict, Optional

# Change these values to configure authentication for the plugin
ZULIP_USER = "svn-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"

# commit_notice_destination() lets you customize where commit notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * path   = the path to the svn repository on the server
# * commit = the commit id
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit except for the "evil-master-plan"
# and "my-super-secret-repository" repos to
# * stream "commits"
# * topic "branch_name"
def commit_notice_destination(path: str, commit: str) -> Optional[Dict[str, str]]:
    repo = path.split("/")[-1]
    if repo not in ["evil-master-plan", "my-super-secret-repository"]:
        return dict(stream="commits", subject=f"{repo}")

    # Return None for cases where you don't want a notice sent
    return None


## If properly installed, the Zulip API should be in your import
## path, but if not, set a custom path below
ZULIP_API_PATH: Optional[str] = None

# Set this to your Zulip server's API URI
ZULIP_SITE = "https://zulip.example.com"
