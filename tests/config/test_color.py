from enum import Enum

from zulipterminal.config.color import color_properties


def test_color_properties() -> None:
    class Color(Enum):
        WHITE = "wh  #256  #24"

    ExpandedColor = color_properties(Color, "BOLD", "ITALICS")

    assert ExpandedColor.WHITE in ExpandedColor
    assert ExpandedColor.WHITE.value == "wh  #256  #24"
    assert ExpandedColor.WHITE__BOLD_ITALICS in ExpandedColor
    assert ExpandedColor.WHITE__BOLD_ITALICS.value == "wh  #256  #24 , bold , italics"
