import urwid
from zulipterminal.ui_tools.views import ModListWalker

def _noop():
    pass

def test_empty_list_no_crash_and_no_negative_focus():
    wl = ModListWalker(contents=[], action=_noop)
    wl._set_focus(0)  # 不应抛异常
    assert len(wl) == 0
    assert getattr(wl, "_focus", 0) == 0

def test_oob_focus_is_clamped_to_valid_range():
    items = [urwid.Text("a"), urwid.Text("b")]
    wl = ModListWalker(contents=items, action=_noop)
    wl._set_focus(9999)  # 越界→应夹到 len-1
    assert getattr(wl, "_focus", None) == len(wl) - 1

def test_negative_focus_is_clamped_to_zero():
    items = [urwid.Text("x")]
    wl = ModListWalker(contents=items, action=_noop)
    wl._set_focus(-42)  # 负数→应夹到 0
    assert getattr(wl, "_focus", None) == 0
