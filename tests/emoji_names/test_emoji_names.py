from zulipterminal.emoji_names import EMOJI_NAMES


def test_generated_emoji_list_sorted():
    assert EMOJI_NAMES == sorted(EMOJI_NAMES)


def test_emojis_fixture_sorted(emojis_fixture):
    assert emojis_fixture == sorted(emojis_fixture)
