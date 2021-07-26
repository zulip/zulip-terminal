# Referred and translated from zulip/static/shared/js/fenced_code.js
# Example: ```quote\nThis is a quote.\n```
REGEX_QUOTED_FENCE_LENGTH = r"^ {0,3}(`{3,})"


# Example: #fff
REGEX_COLOR_3_DIGIT = r"^#[0-9A-Fa-f]{3}$"
# Example: #ffffff
REGEX_COLOR_6_DIGIT = r"^#[0-9A-Fa-f]{6}$"


# Example: example-user@zulip.com
REGEX_RECIPIENT_EMAIL = r"[\w\.-]+@[\w\.-]+"
# Example: Test User <example-user@zulip.com>
REGEX_CLEANED_RECIPIENT = r"^(.*?)(?:\s*?<?({})>?(.*))?$".format(REGEX_RECIPIENT_EMAIL)
