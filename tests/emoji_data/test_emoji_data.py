from zulipterminal.unicode_emojis import EMOJI_DATA


def test_generated_emoji_list_sorted():
    assert EMOJI_DATA == sorted(EMOJI_DATA)


def test_unicode_emojis_fixture_sorted(unicode_emojis):
    assert unicode_emojis == sorted(unicode_emojis)
