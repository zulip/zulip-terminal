from enum import Enum

from zulipterminal.config.color import color_properties


def test_color_properties():
    class Color(Enum):
        WHITE = "wh  #256  #24"

    Color = color_properties(Color, "BOLD", "ITALICS")

    assert Color.WHITE in Color
    assert Color.WHITE.value == "wh  #256  #24"
    assert Color.WHITE__BOLD_ITALICS in Color
    assert Color.WHITE__BOLD_ITALICS.value == "wh  #256  #24 , bold , italics"
