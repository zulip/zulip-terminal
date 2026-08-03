"""
Fixed sizes of UI elements
"""

TAB_WIDTH = 3
LEFT_WIDTH = 31
RIGHT_WIDTH = 23

# These affect popup width-scaling, dependent upon window width
# At and below this width, popup is window width:
MIN_SUPPORTED_POPUP_WIDTH = 80
# Until this width, popup scales linearly upwards with width
MAX_LINEAR_SCALING_WIDTH = 100
# Above that width, popup increases as 3/4 of window width
