
# ZT : THEME CONTRIBUTION GUIDE

This document explains how Zulip Terminal manages themes.

ZT uses theme-files to define a particular theme which can be found in the `zulipterminal/themes` folder.

> **TIP**: For a theme to be accepted, it has to pass certain tests. The easiest way to make sure you have all the styles, format and spacing correct is to copy-paste an existing theme and then edit them but to understand more, read on!

## COLOR SCHEME

> Zulip creates some default color schemes for use in themes which can be found in `color.py`. These colors also make use of the BOLD property, more on which in the next section. Make sure if any of the existing color schemes from any of the existing themes can be useful.

To use the default bold color scheme in a theme, paste this line at the top of the file:

```python
from zulipterminal.config.color import DefaultBoldColor as Color
```

If BOLD is something that is not needed, just use:

```python
from zulipterminal.config.color import DefaultColor as Color
```

Likewise, to use a color scheme from any other theme like Gruvbox (for which the colors are defined in colors_gruvbox.py), use:

```python
from zulipterminal.themes.colors_gruvbox import DefaultBoldColor
```

---

If any of these are not enough for the theme that you want to create, the following format would give an idea of how to create a new color scheme ( Refer: `colors_gruvbox.py` ).

```python
class ThemeColor(Enum):
    WHITE = '16code   256code   24code'
    ...
```

We use **Enum** to define color constants.
Each color constant is a string containing 3 space separated
color codes:

* **16code**: Terminal's default 16 color aliases.
  * Only those used in DefaultColor are acceptable.
  * Eg: `black, light_cyan, etc`
* **256code**: High color, 256 color code.
  * Acceptable formats: `#000-#fff`, `h0-h255`, `g0-g100`, `g#00-g#ff`
  * Eg: `#rgb or h255 or g19`
* **24code**: True color, 24 bit color code.
  * Similar to HTML colors.
  * Eg: `#rrggbb`

`'default'` is a special alias which uses the default
foreground or background.

### COLOR PROPERTIES

The `color_properties()` function adds special properties like
Bold, Italics, Strikethrough, etc to the color scheme.

```python
Color = color_properties(ThemeColor, 'BOLD', 'ITALICS', 'STRIKETHROUGH')
```

**Note**: It is advisable to only use BOLD as of now, similar to `DefaultBoldColor`, to support as many terminals as possible.

## THEME STYLE

To use these colors in a theme style use the dot notation:

```python
(Color.BLACK, Color.DARK_CYAN)
```

Everything after a Dunder or Double Underscore
are considered as properties.

```python
(Color.YELLOW__BOLD, Color.LIGHT_CYAN__BOLD_ITALICS)
```

The actual styles are defined in a dictionary called STYLES
which takes the style as the key and a tuple with foreground
and background as the value.

```python
STYLES = {
    # style_name   :  foreground     background
    'selected'     : (Color.BLACK,  Color.LIGHT_GREEN)
    ...
}
```

The REQUIRED_STYLES dictionary in `config/themes.py` shows all the required styles needed for a theme to be considered complete and pass tests but as mentioned above it is best to copy-paste an existing theme
and then edit it.

If there are any issues, feel free to bring it up on [#zulip-terminal](https://chat.zulip.org/#narrow/stream/206-zulip-terminal)
