import pytest

from urwid_readline import ReadlineEdit


@pytest.mark.parametrize("set_pos, end_pos", [(100, 3), (-1, 0)])
def test_edit_pos_clamp(set_pos, end_pos):
    edit = ReadlineEdit(edit_text="asd", edit_pos=0)
    assert edit.edit_pos == 0
    edit.edit_pos = set_pos
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [("ab", 2, 1), ("ab", 1, 0), ("ab", 0, 0)],
)
def test_backward_char(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.backward_char()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [("ab", 0, 1), ("ab", 1, 2), ("ab", 2, 2)],
)
def test_forward_char(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.forward_char()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [
        ("ab", 2, 0),
        ("ab", 1, 0),
        ("line 1\nline 2", 13, 7),
        ("line 1\nline 2", 8, 7),
        ("line 1\nline 2", 7, 0),
        ("line 1\nline 2", 6, 0),
        ("line 1\nline 2", 1, 0),
        ("line 1\nline 2", 0, 0),
    ],
)
def test_beginnining_of_line(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.beginning_of_line()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [
        ("ab", 0, 2),
        ("ab", 1, 2),
        ("ab", 2, 2),
        ("line 1\nline 2", 0, 6),
        ("line 1\nline 2", 1, 6),
        ("line 1\nline 2", 5, 6),
        ("line 1\nline 2", 6, 13),
        ("line 1\nline 2", 7, 13),
        ("line 1\nline 2", 8, 13),
        ("line 1\nline 2", 13, 13),
    ],
)
def test_end_of_line(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.end_of_line()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [
        ("'x'", 3, 1),
        ("'x'", 2, 1),
        ("'x'", 1, 0),
        ("'x'", 0, 0),
        ("'x' x", 4, 1),
        ("'x' x", 3, 1),
        ("'x' x", 2, 1),
        ("'x' x", 1, 0),
        ("'x'' x", 5, 1),
        ("'x'' x", 4, 1),
        ("'x'' x", 3, 1),
        ("'x'' x", 2, 1),
        ("'x'' x", 1, 0),
        ("'x'' x'", 6, 5),
        ("'x'' x'", 5, 1),
        ("'x'' x'", 4, 1),
        ("'x'' x'", 3, 1),
        ("'x'' x'", 2, 1),
        ("'x'' x'", 1, 0),
        ("xx'xx x", 7, 6),
        ("xx'xx x", 6, 3),
        ("xx'xx x", 3, 0),
    ],
)
def test_backward_word(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.backward_word()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [
        ("'x'", 0, 1),
        ("'x'", 1, 3),
        ("'x'", 2, 3),
        ("'x'", 3, 3),
        ("'x' x", 1, 4),
        ("'x' x", 2, 4),
        ("'x' x", 3, 4),
        ("'x' x", 4, 5),
        ("'x'' x", 1, 5),
        ("'x'' x", 2, 5),
        ("'x'' x", 3, 5),
        ("'x'' x", 4, 5),
        ("'x'' x", 5, 6),
        ("'x'' x'", 1, 5),
        ("'x'' x'", 2, 5),
        ("'x'' x'", 3, 5),
        ("'x'' x'", 4, 5),
        ("'x'' x'", 5, 7),
        ("'x'' x'", 6, 7),
        ("xx'xx x", 0, 3),
        ("xx'xx x", 3, 6),
    ],
)
def test_forward_word(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.forward_word()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("abc", 0, "bc", 0),
        ("abc", 1, "ac", 1),
        ("abc", 2, "ab", 2),
        ("abc", 3, "abc", 3),
    ],
)
def test_delete_char(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.delete_char()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("abc", 3, "ab", 2),
        ("abc", 2, "ac", 1),
        ("abc", 1, "bc", 0),
        ("abc", 0, "abc", 0),
    ],
)
def test_backward_delete_char(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.backward_delete_char()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [
        ("ab", 0, 0),
        ("ab", 1, 1),
        ("ab", 2, 2),
        ("line 1\nline 2", 13, 6),
        ("line 1\nline 2", 8, 1),
        ("line 1\nline 2", 7, 0),
        ("line 1\nline 2", 6, 6),
        ("line 1\nline 2", 1, 1),
        ("line 1\nline 2", 0, 0),
    ],
)
def test_previous_line(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.previous_line()
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_pos",
    [
        ("ab", 0, 0),
        ("ab", 1, 1),
        ("ab", 2, 2),
        ("line 1\nline 2", 0, 7),
        ("line 1\nline 2", 1, 8),
        ("line 1\nline 2", 6, 13),
        ("line 1\nline 2", 7, 7),
        ("line 1\nline 2", 8, 8),
        ("line 1\nline 2", 13, 13),
    ],
)
def test_next_line(start_text, start_pos, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.next_line()
    assert edit.edit_pos == end_pos


def test_clear_screen():
    edit = ReadlineEdit(edit_text="line 1\nline 2", edit_pos=4)
    edit.clear_screen()
    assert edit.edit_pos == 0
    assert edit.edit_text == ""


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("", 0, "", 0),
        ("ab", 1, "b", 0),
        ("line 1\nline 2", 0, "line 1\nline 2", 0),
        ("line 1\nline 2", 1, "ine 1\nline 2", 0),
        ("line 1\nline 2", 6, "\nline 2", 0),
        ("line 1\nline 2", 7, "line 1\nline 2", 7),
        ("line 1\nline 2", 8, "line 1\nine 2", 7),
        ("line 1\nline 2", 13, "line 1\n", 7),
        ("line 1\nline 2\nline 3", 7, "line 1\nline 2\nline 3", 7),
        ("line 1\nline 2\nline 3", 8, "line 1\nine 2\nline 3", 7),
        ("line 1\nline 2\nline 3", 13, "line 1\n\nline 3", 7),
    ],
)
def test_backward_kill_line(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.backward_kill_line()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("", 0, "", 0),
        ("ab", 1, "a", 1),
        ("line 1\nline 2", 0, "\nline 2", 0),
        ("line 1\nline 2", 1, "l\nline 2", 1),
        ("line 1\nline 2", 6, "line 1\nline 2", 6),
        ("line 1\nline 2", 7, "line 1\n", 7),
        ("line 1\nline 2", 8, "line 1\nl", 8),
        ("line 1\nline 2", 13, "line 1\nline 2", 13),
        ("line 1\nline 2\nline 3", 7, "line 1\n\nline 3", 7),
        ("line 1\nline 2\nline 3", 8, "line 1\nl\nline 3", 8),
        ("line 1\nline 2\nline 3", 13, "line 1\nline 2\nline 3", 13),
    ],
)
def test_forward_kill_line(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.forward_kill_line()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("", 0, "", 0),
        ("ab", 1, "", 0),
        ("line 1\nline 2", 0, "\nline 2", 0),
        ("line 1\nline 2", 6, "\nline 2", 0),
        ("line 1\nline 2", 7, "line 1\n", 7),
        ("line 1\nline 2", 13, "line 1\n", 7),
        ("line 1\nline 2\nline 3", 7, "line 1\n\nline 3", 7),
        ("line 1\nline 2\nline 3", 8, "line 1\n\nline 3", 7),
        ("line 1\nline 2\nline 3", 13, "line 1\n\nline 3", 7),
    ],
)
def test_kill_whole_line(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.kill_whole_line()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("'x'", 3, "'", 1),
        ("'x'", 2, "''", 1),
        ("'x'", 1, "x'", 0),
        ("'x'", 0, "'x'", 0),
        ("'x' x", 4, "'x", 1),
        ("'x' x", 3, "' x", 1),
        ("'x' x", 2, "'' x", 1),
        ("'x' x", 1, "x' x", 0),
        ("'x'' x", 5, "'x", 1),
        ("'x'' x", 4, "' x", 1),
        ("'x'' x", 3, "'' x", 1),
        ("'x'' x", 2, "''' x", 1),
        ("'x'' x", 1, "x'' x", 0),
        ("'x'' x'", 6, "'x'' '", 5),
        ("'x'' x'", 5, "'x'", 1),
        ("'x'' x'", 4, "' x'", 1),
        ("'x'' x'", 3, "'' x'", 1),
        ("'x'' x'", 2, "''' x'", 1),
        ("'x'' x'", 1, "x'' x'", 0),
        ("xx'xx x", 7, "xx'xx ", 6),
        ("xx'xx x", 6, "xx'x", 3),
        ("xx'xx x", 3, "xx x", 0),
    ],
)
def test_backward_kill_word(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.backward_kill_word()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("'x'", 1, "'", 1),
        ("'x'", 2, "'x", 2),
        ("'x'", 3, "'x'", 3),
        ("'x' x", 1, "'x", 1),
        ("'x' x", 2, "'xx", 2),
        ("'x' x", 3, "'x'x", 3),
        ("'x' x", 4, "'x' ", 4),
        ("'x'' x", 1, "'x", 1),
        ("'x'' x", 2, "'xx", 2),
        ("'x'' x", 3, "'x'x", 3),
        ("'x'' x", 4, "'x''x", 4),
        ("'x'' x", 5, "'x'' ", 5),
        ("'x'' x'", 1, "'x'", 1),
        ("'x'' x'", 2, "'xx'", 2),
        ("'x'' x'", 3, "'x'x'", 3),
        ("'x'' x'", 4, "'x''x'", 4),
        ("'x'' x'", 5, "'x'' ", 5),
        ("'x'' x'", 6, "'x'' x", 6),
        ("xx'xx x", 0, "xx x", 0),
        ("xx'xx x", 3, "xx'x", 3),
    ],
)
def test_kill_word(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.kill_word()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.mark.parametrize(
    "start_text, start_pos, end_text, end_pos",
    [
        ("a", 0, "a", 1),
        ("a", 1, "a", 1),
        ("abc", 0, "bac", 2),
        ("abc", 1, "bac", 2),
        ("abc", 2, "acb", 3),
        ("abc", 3, "acb", 3),
        ("line 1\nline 2", 6, "line1 \nline 2", 6),
        ("line 1\nline 2", 7, "line 1\nilne 2", 9),
        ("line 1\nline 2", 8, "line 1\nilne 2", 9),
        ("line 1\nline 2", 9, "line 1\nlnie 2", 10),
        ("line 1\nline 2", 10, "line 1\nlien 2", 11),
        ("line 1\nline 2", 13, "line 1\nline2 ", 13),
    ],
)
def test_transpose(start_text, start_pos, end_text, end_pos):
    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    edit.transpose_chars()
    assert edit.text == end_text
    assert edit.edit_pos == end_pos


@pytest.fixture
def completion_func_for_source():
    def _factory(source):
        def compl(text, state):
            tmp = (
                [c for c in source if c and c.startswith(text)]
                if text
                else source
            )
            try:
                return tmp[state]
            except (IndexError, TypeError):
                return None

        return compl

    return _factory


@pytest.mark.parametrize(
    "start_text, start_pos, source, positions",
    [
        (
            "",
            0,
            ["start", "stop", "next"],
            [("start", 5), ("stop", 4), ("next", 4), ("", 0), ("start", 5)],
        ),
        (
            "non-matching",
            12,
            ["start", "stop", "next"],
            [("non-matching", 12), ("non-matching", 12)],
        ),
        (
            "s",
            1,
            ["start", "stop", "next"],
            [("start", 5), ("stop", 4), ("s", 1)],
        ),
        (
            "trailing",
            0,
            ["start", "stop", "next"],
            [
                ("starttrailing", 5),
                ("stoptrailing", 4),
                ("nexttrailing", 4),
                ("trailing", 0),
            ],
        ),
        (
            "trailing trailing",
            0,
            ["start", "stop", "next"],
            [
                ("starttrailing trailing", 5),
                ("stoptrailing trailing", 4),
                ("nexttrailing trailing", 4),
                ("trailing trailing", 0),
            ],
        ),
        (
            "strailing trailing",
            1,
            ["start", "stop", "next"],
            [
                ("starttrailing trailing", 5),
                ("stoptrailing trailing", 4),
                ("strailing trailing", 1),
            ],
        ),
        (
            "preceding s",
            11,
            ["start", "stop", "next"],
            [
                ("preceding start", 15),
                ("preceding stop", 14),
                ("preceding s", 11),
            ],
        ),
        (
            "multiline\npreceding s\ntrailing",
            21,
            ["start", "stop", "next"],
            [
                ("multiline\npreceding start\ntrailing", 25),
                ("multiline\npreceding stop\ntrailing", 24),
                ("multiline\npreceding s\ntrailing", 21),
            ],
        ),
    ],
)
@pytest.mark.parametrize("autocomplete_key", [None, "tab", "ctrl q"])
def test_enable_autocomplete(
    completion_func_for_source,
    start_text,
    start_pos,
    source,
    positions,
    autocomplete_key,
):
    keypress = autocomplete_key if autocomplete_key else "tab"

    compl = completion_func_for_source(source)

    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    kwargs = {}
    if autocomplete_key:
        kwargs["key"] = autocomplete_key
    edit.enable_autocomplete(compl, **kwargs)
    for position in positions:
        expected_text, expected_pos = position
        edit.keypress(None, keypress)
        assert edit.edit_text == expected_text
        assert edit.edit_pos == expected_pos


@pytest.mark.parametrize(
    "start_text, start_pos, edits",
    [
        ("", 0, [("forward", "start", 5), ("reverse", "", 0)]),
        (
            "",
            0,
            [
                ("reverse", "next", 4),
                ("reverse", "stop", 4),
                ("reverse", "start", 5),
                ("reverse", "", 0),
            ],
        ),
        (
            "",
            0,
            [
                ("forward", "start", 5),
                ("forward", "stop", 4),
                ("forward", "next", 4),
                ("reverse", "stop", 4),
            ],
        ),
        (
            "",
            0,
            [
                ("forward", "start", 5),
                ("forward", "stop", 4),
                ("forward", "next", 4),
                ("forward", "", 0),
                ("forward", "start", 5),
            ],
        ),
        (
            "",
            0,
            [("reverse", "next", 4), ("forward", "", 0)],
        ),
        (
            "st",
            2,
            [
                ("forward", "start", 5),
                ("reverse", "st", 2),
                ("reverse", "stop", 4),
            ],
        ),
    ],
)
@pytest.mark.parametrize(
    "autocomplete_key, autocomplete_key_reverse",
    [
        (None, None),
        ("tab", "shift tab"),
        ("ctrl q", "ctrl m"),
    ],
)
def test_enable_autocomplete_reverse(
    completion_func_for_source,
    start_text,
    start_pos,
    edits,
    autocomplete_key,
    autocomplete_key_reverse,
):
    source = ["start", "stop", "next"]
    keypress = autocomplete_key if autocomplete_key else "tab"
    keypress_reverse = (
        autocomplete_key_reverse if autocomplete_key_reverse else "shift tab"
    )

    compl = completion_func_for_source(source)

    edit = ReadlineEdit(edit_text=start_text, edit_pos=start_pos)
    kwargs = {}
    if autocomplete_key:
        kwargs["key"] = autocomplete_key
    if autocomplete_key_reverse:
        kwargs["key_reverse"] = autocomplete_key_reverse
    edit.enable_autocomplete(compl, **kwargs)

    for direction, expected_text, expected_pos in edits:
        if direction == "forward":
            edit.keypress(None, keypress)
        else:
            edit.keypress(None, keypress_reverse)

        assert edit.edit_text == expected_text
        assert edit.edit_pos == expected_pos


def test_enable_autocomplete_clear_state(completion_func_for_source):
    source = ["start", "stop", "next"]

    compl = completion_func_for_source(source)

    edit = ReadlineEdit(edit_text="s", edit_pos=1)
    edit.enable_autocomplete(compl)
    edit.keypress(edit.size, "tab")
    assert edit.edit_text == "start"
    assert edit.edit_pos == 5
    edit.keypress(edit.size, "home")
    edit.keypress(edit.size, "right")
    assert edit.edit_pos == 1
    edit.keypress(edit.size, "tab")
    assert edit.edit_text == "starttart"
    assert edit.edit_pos == 5


@pytest.mark.parametrize(
    "autocomplete_delimiters, word_separator, final_phrase",
    [
        (None, " ", "firstw firstw secondw"),
        (None, ";", "firstw;firstw;secondw"),
        (";", " ", "firstw secondw"),
        (";", ";", "firstw;firstw;secondw"),
        ("#", " ", "firstw secondw"),
        ("", " ", "firstw secondw"),
        ("", "-", "firstw-secondw"),
    ],
    ids=[
        "default:space/tab/newline/semicolon-space",
        "default:space/tab/newline/semicolon-semicolon",
        "custom:semicolon-space",
        "custom:semicolon-semicolon",
        "custom:hash-space",
        "no delimiters-space",  # matches from start of text box
        "no delimiters-hyphen",  # matches from start of text box
    ],
)
def test_autocomplete_delimiters(
    completion_func_for_source,
    autocomplete_delimiters,
    word_separator,
    final_phrase,
    word1="firstw",
    word2="secondw",
):
    phrase = word_separator.join([word1, word2])
    phrase_length = len(phrase)

    source = [phrase]

    compl = completion_func_for_source(source)

    edit = ReadlineEdit(edit_text=word1, edit_pos=len(word1))
    edit.enable_autocomplete(compl)
    if autocomplete_delimiters is not None:
        edit.set_completer_delims(autocomplete_delimiters)

    # Completion from word1 to phrase
    edit.keypress(edit.size, "tab")
    assert edit.edit_text == phrase
    assert edit.edit_pos == phrase_length

    # Backspace to after word1 + space
    for _ in range(len(word2)):
        edit.keypress(edit.size, "backspace")
    assert edit.edit_text == word1 + word_separator
    assert edit.edit_pos == len(word1) + 1

    # Completion from word1 + word_separator
    edit.keypress(edit.size, "tab")
    assert edit.edit_text == final_phrase
    assert edit.edit_pos == len(final_phrase)


@pytest.mark.parametrize(
    "keys, expected_edit_pos, expected_text",
    [
        ([], 0, ""),
        (["F"], 0, ""),
        (["F", "O"], 1, "F"),
        (["F", "O", "O"], 2, "FO"),
        (["F", "O", "O", "ctrl w"], 3, "FOO"),
        (["F", "O", "O", "ctrl w", "ctrl _"], 2, "FO"),
        (["a", "s", "d", "ctrl u", "ctrl u"], 3, "asd"),
    ],
)
def test_undo(keys, expected_edit_pos, expected_text):
    edit = ReadlineEdit()
    for key in keys:
        edit.keypress(edit.size, key)
    edit.undo()
    assert edit.edit_pos == expected_edit_pos
    assert edit.text == expected_text


@pytest.mark.parametrize(
    "paste_buffer, text, max_char, pos, expected_pos, expected_text",
    [
        (["OO"], "F", None, 1, 3, "FOO"),
        (["BOO", "FOO"], "", None, 0, 3, "FOO"),
        (["BCDE"], "A", 3, 1, 3, "ABC"),
        (["FOO", "BOO", "FOOBAR"], "", 3, 0, 3, "FOO"),
        (["FOOBAR"], "BAR", 3, 0, 0, "BAR"),
    ],
)
def test_paste(paste_buffer, text, max_char, pos, expected_pos, expected_text):
    edit = ReadlineEdit(edit_text=text, max_char=max_char, edit_pos=pos)
    edit._paste_buffer[:] = paste_buffer
    edit.paste()
    assert edit.edit_pos == expected_pos
    assert edit.edit_text == expected_text


@pytest.mark.parametrize(
    "text, key, max_char, pos, expected_pos, expected_text",
    [
        ("FOAA", "S", None, 4, 5, "FOAAS"),
        ("FOOBAR", "A", 3, 3, 3, "FOO"),
        ("OO", "F", 3, 0, 1, "FOO"),
        ("ABCDE", "F", 4, 3, 3, "ABCD"),
    ],
)
def test_insert_char_at_cursor(
    text, key, max_char, pos, expected_pos, expected_text
):
    edit = ReadlineEdit(edit_text=text, max_char=max_char, edit_pos=pos)
    edit._insert_char_at_cursor(key)
    assert edit.edit_pos == expected_pos
    assert edit.edit_text == expected_text
