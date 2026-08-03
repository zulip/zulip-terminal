# https://github.com/python/mypy/issues/1141
from typing import Dict, Optional

# Change these values to configure authentication for the plugin
ZULIP_USER = "openshift-bot@example.com"
ZULIP_API_KEY = "0123456789abcdef0123456789abcdef"

# deployment_notice_destination() lets you customize where deployment notices
# are sent to with the full power of a Python function.
#
# It takes the following arguments:
# * branch = the name of the branch where the deployed commit was
#            pushed to
#
# Returns a dictionary encoding the stream and subject to send the
# notification to (or None to send no notification).
#
# The default code below will send every commit pushed to "main" to
# * stream "deployments"
# * topic "main"
# And similarly for branch "test-post-receive" (for use when testing).
def deployment_notice_destination(branch: str) -> Optional[Dict[str, str]]:
    if branch in ["main", "master", "test-post-receive"]:
        return dict(stream="deployments", subject=f"{branch}")

    # Return None for cases where you don't want a notice sent
    return None


# Modify this function to change how deployments are displayed
#
# It takes the following arguments:
# * app_name  = the name of the app being deployed
# * url       = the FQDN (Fully Qualified Domain Name) where the app
#                can be found
# * branch    = the name of the branch where the deployed commit was
#                pushed to
# * commit_id = hash of the commit that triggered the deployment
# * dep_id    = deployment id
# * dep_time  = deployment timestamp
def format_deployment_message(
    app_name: str = "",
    url: str = "",
    branch: str = "",
    commit_id: str = "",
    dep_id: str = "",
    dep_time: str = "",
) -> str:
    return f"Deployed commit `{commit_id}` ({branch}) in [{app_name}]({url})"


## If properly installed, the Zulip API should be in your import
## path, but if not, set a custom path below
ZULIP_API_PATH = None  # type: Optional[str]

# Set this to your Zulip server's API URI
ZULIP_SITE = "https://zulip.example.com"
