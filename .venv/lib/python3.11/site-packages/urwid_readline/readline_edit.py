import contextlib
import re
import string

import urwid


def _is_valid_key(char):
    return urwid.is_wide_char(char, 0) or (
        len(char) == 1 and ord(char) >= 32
    )


class AutocompleteState:
    def __init__(self, prefix, infix, suffix, cycle_forward):
        self.prefix = prefix
        self.infix = infix
        self.suffix = suffix
        self.num = 0 if cycle_forward else -1


class PasteBuffer(list):
    def append(self, text):
        if not len(text):
            return
        super().append(text)


class UndoState:
    def __init__(self, edit_pos, edit_text):
        self.edit_pos = edit_pos
        self.edit_text = edit_text


class UndoBuffer:
    def __init__(self):
        self.pos = 0
        self.buffer = []

    @property
    def empty(self):
        return self.pos == 0

    @property
    def cur(self):
        return self.buffer[self.pos - 1]

    def push(self, old_state, new_state):
        self.buffer = self.buffer[: self.pos]
        if old_state.edit_text != new_state.edit_text:
            self.buffer.append((old_state, new_state))
        self.pos = len(self.buffer)

    def pop(self):
        if not self.empty:
            self.pos -= 1


class ReadlineEdit(urwid.Edit):
    ignore_focus = False

    def __init__(
        self,
        *args,
        word_chars=string.ascii_letters + string.digits + "_",
        max_char=None,
        **kwargs
    ):
        if max_char and "edit_text" in kwargs:
            kwargs["edit_text"] = kwargs["edit_text"][:max_char]
        super().__init__(*args, **kwargs)
        self._word_regex1 = re.compile(
            "([%s]+)" % "|".join(re.escape(ch) for ch in word_chars)
        )
        self._word_regex2 = re.compile(
            "([^%s]+)" % "|".join(re.escape(ch) for ch in word_chars)
        )
        self._autocomplete_state = None
        self._autocomplete_func = None
        self._autocomplete_key = None
        self._autocomplete_key_reverse = None
        self._autocomplete_delims = " \t\n;"
        self._max_char = max_char
        self._paste_buffer = PasteBuffer()
        self._undo_buffer = UndoBuffer()
        self.size = (30,)  # SET MAXCOL DEFAULT VALUE

        self.keymap = {
            "ctrl f": self.forward_char,
            "ctrl b": self.backward_char,
            "ctrl a": self.beginning_of_line,
            "ctrl e": self.end_of_line,
            "home": self.beginning_of_line,
            "end": self.end_of_line,
            "meta f": self.forward_word,
            "meta b": self.backward_word,
            "shift right": self.forward_word,
            "shift left": self.backward_word,
            "ctrl d": self.delete_char,
            "ctrl h": self.backward_delete_char,
            "delete": self.delete_char,
            "backspace": self.backward_delete_char,
            "ctrl u": self.backward_kill_line,
            "ctrl k": self.forward_kill_line,
            "meta x": self.kill_whole_line,
            "meta d": self.kill_word,
            "ctrl w": self.backward_kill_word,
            "meta backspace": self.backward_kill_word,
            "ctrl t": self.transpose_chars,
            "ctrl l": self.clear_screen,
            "ctrl y": self.paste,
            "ctrl _": self.undo,
        }

        if self.multiline:
            self.keymap.update(
                {
                    "enter": self.insert_new_line,
                }
            )

    def keypress(self, size, key):
        self.size = size
        if key == self._autocomplete_key and self._autocomplete_func:
            self._complete(True)
            return None
        elif key == self._autocomplete_key_reverse and self._autocomplete_func:
            self._complete(False)
            return None
        else:
            self._autocomplete_state = None

        if key == "right":
            return None if self.forward_char() else key

        if key == "left":
            return None if self.backward_char() else key

        if key == "up" or key == "ctrl p":
            return None if self.previous_line() else key

        if key == "down" or key == "ctrl n":
            return None if self.next_line() else key

        if key in self.keymap:
            if self.keymap[key] == self.undo:
                self.keymap[key]()
            else:
                with self._capture_undo():
                    self.keymap[key]()
            self._invalidate()
            return None
        elif _is_valid_key(key):
            with self._capture_undo():
                self._insert_char_at_cursor(key)
            self._invalidate()
            return None
        return key

    def _insert_char_at_cursor(self, key):
        if self._max_char and len(self.edit_text) == self._max_char:
            return

        self.set_edit_text(
            self._edit_text[0 : self._edit_pos]
            + key
            + self._edit_text[self._edit_pos :]
        )
        self.set_edit_pos(self._edit_pos + 1)

    def clear_screen(self):
        self.set_edit_pos(0)
        self.set_edit_text("")

    def _make_undo_state(self):
        return UndoState(self.edit_pos, self.edit_text)

    def _apply_undo_state(self, state):
        self.set_edit_text(state.edit_text)
        self.set_edit_pos(state.edit_pos)

    @contextlib.contextmanager
    def _capture_undo(self):
        old_state = self._make_undo_state()
        yield
        new_state = self._make_undo_state()
        self._undo_buffer.push(old_state, new_state)

    def undo(self):
        if self._undo_buffer.empty:
            return
        old_state, new_state = self._undo_buffer.cur
        self._undo_buffer.pop()
        self._apply_undo_state(old_state)

    def paste(self):
        # do not paste if empty buffer
        if not len(self._paste_buffer):
            return

        text = self._paste_buffer[-1]
        if self._max_char:
            chars_left = self._max_char - len(self.edit_text)
            text = text[:chars_left]

        self.set_edit_text(
            self.edit_text[: self.edit_pos]
            + text
            + self.edit_text[self.edit_pos :]
        )
        self.set_edit_pos(self.edit_pos + len(text))

    def previous_line(self):
        x, y = self.get_cursor_coords(self.size)
        return self.move_cursor_to_coords(self.size, x, y - 1)

    def next_line(self):
        x, y = self.get_cursor_coords(self.size)
        return self.move_cursor_to_coords(self.size, x, y + 1)

    def backward_char(self):
        if self._edit_pos > 0:
            self.set_edit_pos(self._edit_pos - 1)
            return True
        return False

    def forward_char(self):
        if self._edit_pos < len(self._edit_text):
            self.set_edit_pos(self._edit_pos + 1)
            return True
        return False

    def backward_word(self):
        for match in self._word_regex1.finditer(
            self._edit_text[0 : self._edit_pos][::-1]
        ):
            self.set_edit_pos(self._edit_pos - match.end(1))
            return
        self.set_edit_pos(0)

    def forward_word(self):
        for match in self._word_regex2.finditer(
            self._edit_text[self._edit_pos :]
        ):
            self.set_edit_pos(self._edit_pos + match.end(1))
            return
        self.set_edit_pos(len(self._edit_text))

    def delete_char(self):
        if self._edit_pos < len(self._edit_text):
            self.set_edit_text(
                self._edit_text[0 : self._edit_pos]
                + self._edit_text[self._edit_pos + 1 :]
            )

    def backward_delete_char(self):
        if self._edit_pos > 0:
            self.set_edit_pos(self._edit_pos - 1)
            self.set_edit_text(
                self._edit_text[0 : self._edit_pos]
                + self._edit_text[self._edit_pos + 1 :]
            )

    def backward_kill_line(self):
        for pos in reversed(range(0, self.edit_pos)):
            if self.edit_text[pos] == "\n":
                self._paste_buffer.append(
                    self.edit_text[pos + 1 : self.edit_pos]
                )
                self.set_edit_text(
                    self._edit_text[: pos + 1]
                    + self._edit_text[self.edit_pos :]
                )
                self.edit_pos = pos + 1
                return
        self._paste_buffer.append(self.edit_text[: self.edit_pos])
        self.set_edit_text(self._edit_text[self.edit_pos :])
        self.edit_pos = 0

    def forward_kill_line(self):
        for pos in range(self.edit_pos, len(self.edit_text)):
            if self.edit_text[pos] == "\n":
                self._paste_buffer.append(self.edit_text[self.edit_pos : pos])
                self.set_edit_text(
                    self._edit_text[: self.edit_pos] + self._edit_text[pos:]
                )
                return
        self._paste_buffer.append(self.edit_text[self.edit_pos :])
        self.set_edit_text(self._edit_text[: self.edit_pos])

    def kill_whole_line(self):
        buffer_length = len(self._paste_buffer)
        self.backward_kill_line()
        self.forward_kill_line()
        if len(self._paste_buffer) - buffer_length == 2:
            # if text was added from both forward and backward kill
            self._paste_buffer[:2] = ["".join(self._paste_buffer[:2])]

    def backward_kill_word(self):
        pos = self._edit_pos
        self.backward_word()
        self._paste_buffer.append(self._edit_text[self.edit_pos : pos])
        self.set_edit_text(
            self._edit_text[: self._edit_pos] + self._edit_text[pos:]
        )

    def kill_word(self):
        pos = self._edit_pos
        self.forward_word()
        self._paste_buffer.append(self.edit_text[pos : self.edit_pos])
        self.set_edit_text(
            self._edit_text[0:pos] + self._edit_text[self._edit_pos :]
        )
        self.set_edit_pos(pos)

    def beginning_of_line(self):
        x, y = self.get_cursor_coords(self.size)
        if x == 0 and y > 0:
            y -= 1
        self.move_cursor_to_coords(self.size, 0, y)

    def end_of_line(self):
        text_length = len(self.edit_text)
        # Move one character forward if at the end of a line.
        if (
            self.edit_pos < text_length
            and self.edit_text[self.edit_pos] == "\n"
        ):
            self.forward_char()
        # Set the position of cursor at the next '\n'.
        for pos in range(self.edit_pos, text_length + 1):
            if pos == text_length:
                self.set_edit_pos(pos)
                return
            elif self.edit_text[pos] == "\n":
                self.set_edit_pos(pos)
                return

    def transpose_chars(self):
        x, y = self.get_cursor_coords(self.size)
        x = max(2, x + 1)
        self.move_cursor_to_coords(self.size, x, y)
        x, y = self.get_cursor_coords(self.size)
        if x == 1:
            # Don't transpose in case of single character
            return
        self.set_edit_text(
            self._edit_text[0 : self._edit_pos - 2]
            + self._edit_text[self._edit_pos - 1]
            + self._edit_text[self._edit_pos - 2]
            + self._edit_text[self._edit_pos :]
        )

    def insert_new_line(self):
        if self.multiline:
            self.insert_text("\n")

    def enable_autocomplete(self, func, key="tab", key_reverse="shift tab"):
        self._autocomplete_func = func
        self._autocomplete_key = key
        self._autocomplete_key_reverse = key_reverse
        self._autocomplete_state = None

    def set_completer_delims(self, delimiters):
        self._autocomplete_delims = delimiters

    def _complete(self, cycle_forward):
        if self._autocomplete_state:
            if self._autocomplete_state.num == 0 and not cycle_forward:
                self._autocomplete_state.num = None
            elif self._autocomplete_state.num == -1 and cycle_forward:
                self._autocomplete_state.num = None
            else:
                self._autocomplete_state.num += 1 if cycle_forward else -1
        else:
            text_before_caret = self.edit_text[0 : self.edit_pos]
            text_after_caret = self.edit_text[self.edit_pos :]

            if self._autocomplete_delims:
                group = re.escape(self._autocomplete_delims)
                match = re.match(
                    "^(?P<prefix>.*[" + group + "])(?P<infix>.*?)$",
                    text_before_caret,
                    flags=re.M | re.DOTALL,
                )
                if match:
                    prefix = match.group("prefix")
                    infix = match.group("infix")
                else:
                    prefix = ""
                    infix = text_before_caret
            else:
                match = re.match(
                    "^(?P<infix>.*?)$",
                    text_before_caret,
                    flags=re.M | re.DOTALL,
                )
                prefix = ""
                if match:
                    infix = match.group("infix")
                else:
                    infix = text_before_caret

            suffix = text_after_caret

            self._autocomplete_state = AutocompleteState(
                prefix, infix, suffix, cycle_forward
            )

        state = self._autocomplete_state

        match = self._autocomplete_func(state.infix, state.num)
        if not match:
            match = state.infix
            self._autocomplete_state = None

        self.edit_text = state.prefix + match + state.suffix
        self.edit_pos = len(state.prefix) + len(match)
