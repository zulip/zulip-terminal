# All regexes with (*) are inspired from webapp's
# zulip/static/js/composebox_typeahead.js


# (*) Stream and topic regexes
REGEX_STREAM_NAME = r"([^*>]+)"
REGEX_TOPIC_NAME = r"([^*]*)"


# (*) Example: #**zulip-terminal
REGEX_STREAM_FENCED_HALF = r"#\*\*{stream}".format(stream=REGEX_STREAM_NAME)
# (*) Example: #**zulip-terminal**
REGEX_STREAM_FENCED = r"#\*\*{stream}\*\*".format(stream=REGEX_STREAM_NAME)
# (*) Example text: #**stream name>Topic name
REGEX_STREAM_AND_TOPIC_FENCED_HALF = f"{REGEX_STREAM_FENCED_HALF}>{REGEX_TOPIC_NAME}$"
# (*) Example text: #**stream name**>Topic name
REGEX_STREAM_AND_TOPIC_FENCED = f"{REGEX_STREAM_FENCED}>{REGEX_TOPIC_NAME}$"
# (*) Example text: #stream name>Topic name
REGEX_STREAM_AND_TOPIC_UNFENCED = f"#{REGEX_STREAM_NAME}>{REGEX_TOPIC_NAME}$"


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
# Example: # #000000-#ffffff or #000-#fff or h0-h255 or g0-g100 or g#00-g#ff
REGEX_COLOR_VALID_FORMATS = (
    "#[\\da-f]{6}|#[\\da-f]{3}|(?:h|g)([\\d]{1,3})|g#[\\da-f]{2}|default$"
)


# Example: 6-test-stream
REGEX_INTERNAL_LINK_STREAM_ID = r"^[0-9]+-"
