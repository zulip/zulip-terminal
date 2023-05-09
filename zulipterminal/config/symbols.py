"""
Terminal characters used to mark particular elements of the user interface
"""

# Unless otherwise noted, all symbols are in:
# - Basic Multilingual Plane (BMP)
# - Unicode v1.1
# Suffix comments indicate: unicode name, codepoint (unicode block, version if not v1.1)

INVALID_MARKER = "✗"  # BALLOT X, U+2717 (Dingbats)
STREAM_MARKER_PRIVATE = "P"
STREAM_MARKER_PUBLIC = "#"
STREAM_MARKER_WEB_PUBLIC = "⊚"  # CIRCLED RING OPERATOR, U+229A (Mathematical operators)
STREAM_TOPIC_SEPARATOR = "▶"  # BLACK RIGHT-POINTING TRIANGLE, U+25B6 (Geometric shapes)

# Range of block options for consideration: '█', '▓', '▒', '░'
# FULL BLOCK U+2588, DARK SHADE U+2593, MEDIUM SHADE U+2592, LIGHT SHADE U+2591

# Separator between messages and 'EDITED'
MESSAGE_CONTENT_MARKER = "▒"  # MEDIUM SHADE, U+2592 (Block elements)

QUOTED_TEXT_MARKER = "░"  # LIGHT SHADE, U+2591 (Block elements)

# Extends from end of recipient details (above messages where recipients differ above)
MESSAGE_HEADER_DIVIDER = "━"  # BOX DRAWINGS HEAVY HORIZONTAL, U+2501 (Box drawing)

# NOTE: CHECK_MARK is not used for resolved topics (that is an API detail)
CHECK_MARK = "✓"  # CHECK MARK, U+2713 (Dingbats)

APPLICATION_TITLE_BAR_LINE = "═"  # BOX DRAWINGS DOUBLE HORIZONTAL, U+2550 (Box drawing)
PINNED_STREAMS_DIVIDER = "-"  # HYPHEN-MINUS, U+002D (Basic latin)
COLUMN_TITLE_BAR_LINE = "━"  # BOX DRAWINGS HEAVY HORIZONTAL, U+2501 (Box drawing)

# NOTE: The '⏱' emoji needs an extra space while rendering. Otherwise, it
# appears to overlap its subsequent text.
# Other tested options are: '⧗' and '⧖'.
# TODO: Try 25F7, WHITE CIRCLE WITH UPPER RIGHT QUADRANT?
TIME_MENTION_MARKER = "⏱ "  # STOPWATCH, U+23F1 (Misc Technical, Unicode 6.0)

MUTE_MARKER = "M"
STATUS_ACTIVE = "●"  # BLACK CIRCLE, U+25CF (Geometric shapes)
STATUS_IDLE = "◒"  # CIRCLE WITH LOWER HALF BLACK, U+25D2 (Geometric shapes)
STATUS_OFFLINE = "○"  # WHITE CIRCLE, U+25CB (Geometric shapes)
STATUS_INACTIVE = "•"  # BULLET, U+2022 (General punctuation)
BOT_MARKER = "♟"  # BLACK CHESS PAWN, U+265F (Misc symbols)

# Unicode 3.2:
AUTOHIDE_TAB_LEFT_ARROW = "❰"  # HEAVY LEFT-POINTING ANGLE BRACKET ORNAMENT, U+2770
AUTOHIDE_TAB_RIGHT_ARROW = "❱"  # HEAVY RIGHT-POINTING ANGLE BRACKET ORNAMENT, U+2771
