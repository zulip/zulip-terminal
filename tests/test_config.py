import pytest

from zulipterminal import config

AVAILABLE_COMMANDS = list(config.KEY_BINDINGS.keys())

USED_KEYS = {key
             for values in config.KEY_BINDINGS.values()
             for key in values['keys']}


@pytest.mark.parametrize('command', AVAILABLE_COMMANDS)
def test_keys_for_command(command):
    assert (config.KEY_BINDINGS[command]['keys'] ==
            config.keys_for_command(command))


@pytest.mark.parametrize('command', ['BLAH'*10])
def test_keys_for_command_invalid_command(command):
    with pytest.raises(config.InvalidCommand):
        config.keys_for_command(command)
