import sys

import urwid
from urwid import set_encoding

from zulipterminal.config import symbols


set_encoding("utf-8")

palette = [
    ("header", "white, bold", "dark blue"),
    ("footer", "black", "white"),
]

symbol_dict = {
    name: symbol
    for name, symbol in vars(symbols).items()
    if not name.startswith("__") and not name.endswith("__")
}
max_symbol_name_length = max([len(name) for name in symbol_dict.keys()])

symbol_names_list = [urwid.Text(name, align="center") for name in symbol_dict.keys()]
symbols_list = [urwid.Text(symbol) for symbol in symbol_dict.values()]

symbols_display_box = urwid.Columns(
    [
        # Allot extra width to the symbol names list to create a neat layout.
        (max_symbol_name_length + 2, urwid.Pile(symbol_names_list)),
        # Allot 2 characters to the symbols list to accommodate symbols needing
        # double character-width to render.
        (2, urwid.Pile(symbols_list)),
    ],
    dividechars=5,
)
columns_length = max_symbol_name_length + 10

line_box = urwid.LineBox(
    symbols_display_box, title="Render Symbols", title_attr="header"
)
info_box = urwid.Text(("footer", " Exit: ^C (ctrl c)"), align="center")
display_box = urwid.Pile([line_box, info_box])

# Allot extra width to the display_box to render a neat layout.
body = urwid.Filler(
    urwid.Padding(display_box, width=columns_length + 5, align="center"),
    valign="middle",
)


def main() -> None:
    try:
        loop = urwid.MainLoop(body, palette)
        loop.run()
    finally:
        sys.exit(0)
