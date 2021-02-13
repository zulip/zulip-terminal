"""
Stores terminal characters used to mark particular
elements of the user interface
"""

STREAM_MARKER_INVALID = '✗'
STREAM_MARKER_PRIVATE = 'P'
STREAM_MARKER_PUBLIC = '#'
STREAM_TOPIC_SEPARATOR = '▶'
# Used as a separator between messages and 'EDITED'
MESSAGE_CONTENT_MARKER = '▒'  # Options are '█', '▓', '▒', '░'
QUOTED_TEXT_MARKER = '░'
MESSAGE_HEADER_DIVIDER = '━'
CHECK_MARK = '✓'
APPLICATION_TITLE_BAR_LINE = '═'
PINNED_STREAMS_DIVIDER = '-'
LIST_TITLE_BAR_LINE = '━'
# NOTE: The '⏱' emoji needs an extra space while rendering. Otherwise, it
# appears to overlap its subsequent text.
TIME_MENTION_MARKER = '⏱ '  # Other tested options are: '⧗' and '⧖'.
MUTE_MARKER = 'M'
STATUS_ACTIVE = '●'
STATUS_IDLE = '◒'
STATUS_OFFLINE = '○'
STATUS_INACTIVE = '•'
