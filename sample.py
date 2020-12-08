# This is a simple program that illustrates different style combinations in urwid.
import urwid

def exit_on_q(key):
	if key in ('q', 'Q'):
		raise urwid.ExitMainLoop()

palette = [
	('bold_and_italic', 'white, bold, italics', 'default'),
	('bold_only', 'white, bold', 'default'),
	('italic_only', 'white, italics', 'default'),
	]


title = urwid.Text(u'Different text styles')
normal = urwid.Text(u'Normal: Hello world')
bold = urwid.Text([u'Bold: ',('bold_only', 'Hello world')])
italic = urwid.Text([u'Italic: ',('italic_only', 'Hello world')])
bold_italic = urwid.Text([u'Bold Italic: ',('bold_and_italic', 'Hello world')])
pile = urwid.Pile([title, urwid.Divider(), normal, bold, italic, bold_italic])
top = urwid.Filler(pile)
loop = urwid.MainLoop(top, palette, unhandled_input=exit_on_q)
loop.run()
