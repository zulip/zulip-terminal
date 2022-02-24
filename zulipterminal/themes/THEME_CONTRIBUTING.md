
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
  * Acceptable names: `default`, `black`, `dark red`, `dark green`, `brown`, `dark blue`, `dark magenta`, `dark cyan`, `dark gray`, `light red`, `light green`, `yellow`, `light blue`, `light magenta`, `light cyan`, `light gray`, `white`
  * Reference link to urwid documentation: https://urwid.org/manual/displayattributes.html#standard-foreground 
* **256code**: High color, 256 color code.
  * Acceptable formats: `#000-#fff`, `h0-h255`, `g0-g100`, `g#00-g#ff`
  * Eg: `#rgb or h255 or g19`
* **24code**: True color, 24 bit color code.
  * Similar to HTML colors.
  * Eg: `#rrggbb`

`'default'` is a special alias which uses the default
foreground or background.

The following table consists of the 16code equivalents of 256 color codes-

| 256 color codes                                                                                                                                                                                                                                                                      | Corresponding 16 color codes | 
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- | 
| `h0`, `h16`, `h232`, `h233`, `h234`, `h235`, `h236`, `h237`                                                                                                                                                                                                                          | `black`                      | 
| `h1`, `h52`, `h88`, `h124`                                                                                                                                                                                                                                                           | `dark red`                   | 
| `h2`, `h22`, `h28`, `h34`, `h72`                                                                                                                                                                                                                                                     | `dark green`                 | 
| `h3`, `h58`, `h64`, `h70`, `h94`, `h100`, `h106`, `h130`, `h136`, `h142`                                                                                                                                                                                                             | `brown`                      | 
| `h4`, `h17`, `h18`, `h19`, `h60`, `h61`, `h67`, `h97`                                                                                                                                                                                                                                | `dark blue`                  | 
| `h5`, `h53`, `h54`, `h55`, `h89`, `h90`, `h91`, `h96`, `h125`, `h126`, `h127`, `h132`, `h133`, `h139`                                                                                                                                                                                | `dark magenta`               | 
| `h6`, `h23`, `h24`, `h25`, `h29`, `h30`, `h31`, `h35`, `h36`, `h37`, `h73`                                                                                                                                                                                                           | `dark cyan`                  | 
| `h7`, `h71`, `h103`, `h107`, `h108`, `h109`, `h114`, `h115`, `h116`, `h131`, `h137`, `h138`, `h143`, `h144`, `h145`, `h146`, `h150`, `h151`, `h152`, `h174`, `h180`, `h181`, `h186`, `h187`, `h188`, `h248`, `h249`, `h250`, `h251`, `h252`, `h253`                                  | `light gray`                 | 
| `h8`, `h59`, `h65`, `h66`, `h95`, `h101`, `h102`, `h238`, `h239`, `h240`, `h241`, `h242`, `h243`, `h244`, `h245`, `h246`, `h247`                                                                                                                                                     | `dark gray`                  | 
| `h9`, `h160`, `h166`, `h167`, `h173`, `h196`, `h202`, `h203`, `h209`, `h215`                                                                                                                                                                                                         | `light red`                  | 
| `h10`, `h40`, `h41`, `h46`, `h47`, `h76`, `h77`, `h78`, `h82`, `h83`, `h84`, `h85`, `h113`, `h119`, `h120`, `h121`, `h155`, `h156`                                                                                                                                                   | `light green`                | 
| `h11`, `h112`, `h118`, `h148`, `h149`, `h154`, `h172`, `h178`, `h179`, `h184`, `h185`, `h190`, `h191`, `h208`, `h214`, `h220`, `h221`, `h226`, `h227`                                                                                                                                | `yellow`                     | 
| `h12`, `h20`, `h21`, `h26`, `h27`, `h56`, `h57`, `h62`, `h63`, `h68`, `h69`, `h75`, `h98`, `h99`, `h104`, `h105`, `h110`, `h111`, `h135`, `h140`, `h141`, `h147`                                                                                                                     | `light blue`                 | 
| `h13`, `h92`, `h93`, `h128`, `h134`, `h129`, `h161`, `h162`, `h163`, `h164`, `h165`, `h168`, `h169`, `h170`, `h171`, `h175`, `h176`, `h177`, `h182`, `h183`, `h197`, `h198`, `h199`, `h200`, `h201`, `h204`, `h205`, `h206`, `h207`, `h211`, `h212`, `h213`, `h218`, `h219`, `h225`  | `light magenta`              | 
| `h14`, `h32`, `h33`, `h38`, `h39`, `h42`, `h43`, `h44`, `h45`, `h48`, `h49`, `h50`, `h51`, `h74`, `h79`, `h80`, `h81`, `h86`, `h87`, `h117`, `h122`, `h123`                                                                                                                          | `light cyan`                 | 
| `h15`, `h153`, `h157`, `h158`, `h159`, `h189`, `h192`, `h193`, `h194`, `h195`, `h210`, `h216`, `h217`, `h222`, `h223`, `h224`, `h228`, `h229`, `h230`, `h231`, `h254`, `h255`                                                                                                        | `white`                      | 

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
