from zulipterminal.emoji_names import EMOJI_NAMES


def test_generated_emoji_list_sorted():
    assert EMOJI_NAMES == sorted(EMOJI_NAMES)
