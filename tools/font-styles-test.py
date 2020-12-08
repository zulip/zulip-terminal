#!/usr/bin/env python3

import urwid

def exit_on_q(key):
	if key in ('q', 'Q'):
		raise urwid.ExitMainLoop()

palette = [
	('normal         ', 'white', 'black'),
	('bold_only      ', 'white, bold', 'black'),
	('italic_only    ', 'white, italics', 'black'),
	('bold_and_italic', 'white, bold, italics', 'black'),
]

text = 'Hello world'
pile = urwid.Pile([urwid.Text([st[0] + u' : ', (st[0], text)])
	               for st in palette])
loop = urwid.MainLoop(urwid.Filler(pile), palette, unhandled_input=exit_on_q)
loop.run()
