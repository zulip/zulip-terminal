import pytest

from zulipterminal import config

AVAILABLE_COMMANDS = list(config.KEY_BINDINGS.keys())

USED_KEYS = {key
             for values in config.KEY_BINDINGS.values()
             for key in values['keys']}
