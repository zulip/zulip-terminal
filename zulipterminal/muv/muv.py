"""
Preview markdown file
"""
import argparse
import json
import logging
import os

import pkg_resources
import urwid
import urwid.raw_display

from .modal import ContentParser, PageListBox
from .util import check_if_italic

CONF_DIR = 'conf'
CONF_FALLBACK_PATH = 'conf'
PALETTE_FILE_NAME = 'palette.json' if check_if_italic(
) else 'palette_without_italics.json'


def load_palette(palette_file):
    """Load palette from json file"""
    palette = []
    if not palette_file:
        for loc in CONF_FALLBACK_PATH:
            try:
                palette_file = os.path.join(loc, PALETTE_FILE_NAME)
                if os.path.exists(palette_file):
                    break
            except Exception:
                pass
        else:
            logging.error(
                "No palette file found, colors and other settings unavailable")
            return palette

    with open(palette_file) as infile:
        attrs = json.load(infile)
        for attr in attrs["palette"]:
            attr = (attr['name'], attr['fg'], attr['bg'],
                    attr['mono'], attr['fgh'], attr['bgh'])
            palette.append(attr)
    return palette


def load_config(config_file):
    """Load configuration from json file"""
    if not config_file:
        for loc in CONF_FALLBACK_PATH:
            try:
                config_file = os.path.join(loc, 'muv.conf')
                if os.path.exists(config_file):
                    break
            except Exception:
                pass
        else:
            logging.info("No config file found")
            return {}
    with open(config_file) as f:
        return json.load(f)


def preview(text, controller, is_message=True, log='CRITICAL', palette=None,
            config_file=None):
    """
    Preview markdown file.

    Positional argument:
    text -- the text to view in markdown
    log -- specify log level, valid options include DEBUG, INFO, WARNING,
           ERROR, CRITICAL
    Keyword arguments:
    palette -- palette file location
    config_file -- json configuration file
    """
    numeric_level = getattr(logging, log, None)
    logging.basicConfig(level=numeric_level,
                        format='%(asctime)s %(levelname)s: %(message)s')
    config = load_config(config_file)
    parser = ContentParser(config=config)
    listbox_content = parser.markdown2markup(text)
    if is_message:
        return listbox_content
    listbox = PageListBox(urwid.SimpleListWalker(listbox_content), controller)
    return urwid.LineBox(listbox, title="Help | Press `q` to quit")
