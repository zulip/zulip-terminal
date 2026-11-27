from typing import Dict, Optional

# Change these values to configure authentication for the plugin
ZULIP_USER = "p4-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"
ZULIP_SITE = "https://zulip.example.com"

# Set this to True to silently drop messages if the destination stream
# does not exist. This prevents the warnings from Zulip's Notification Bot
# when commits are made on a branch for which no stream has been created.
ZULIP_IGNORE_MISSING_STREAM = False

# Set this to point at a p4web installation to get changelist IDs as links
# P4_WEB = "https://p4web.example.com"
P4_WEB: Optional[str] = None

# commit_notice_destination() lets you customize where commit notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * path   = the path to the Perforce depot on the server
# * changelist = the changelist id
#
# Returns a dictionary encoding the stream and topic to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit except for ones in the
# "master-plan" and "secret" subdirectories of //depot/ to:
# * stream "depot_subdirectory-commits"
# * subject "change_root"
def commit_notice_destination(path: str, changelist: int) -> Optional[Dict[str, str]]:
    dirs = path.split("/")
    if len(dirs) >= 4 and dirs[3] not in ("*", "..."):
        directory = dirs[3]
    else:
        # No subdirectory, so just use "depot"
        directory = dirs[2]

    if directory not in ["evil-master-plan", "my-super-secret-repository"]:
        return dict(stream=f"{directory}-commits", subject=path)

    # Return None for cases where you don't want a notice sent
    return None


## If properly installed, the Zulip API should be in your import
## path, but if not, set a custom path below
ZULIP_API_PATH: Optional[str] = None
