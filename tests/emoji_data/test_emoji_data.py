from collections import OrderedDict
from typing import Dict

from zulipterminal.unicode_emojis import EMOJI_DATA


def test_generated_emoji_list_sorted() -> None:
    assert EMOJI_DATA == OrderedDict(sorted(EMOJI_DATA.items()))


def test_unicode_emojis_fixture_sorted(
    unicode_emojis: "OrderedDict[str, Dict[str, str]]",
) -> None:
    assert unicode_emojis == OrderedDict(sorted(unicode_emojis.items()))
