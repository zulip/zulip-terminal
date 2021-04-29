# Referred and translated from zulip/static/shared/js/fenced_code.js
# Example: ```quote\nThis is a quote.\n```
REGEX_QUOTED_FENCE_LENGTH = r"^ {0,3}(`{3,})"


# Example: #fff
REGEX_COLOR_3_DIGIT = r"^#[0-9A-Fa-f]{3}$"
# Example: #ffffff
REGEX_COLOR_6_DIGIT = r"^#[0-9A-Fa-f]{6}$"
