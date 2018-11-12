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


@pytest.mark.parametrize('command', AVAILABLE_COMMANDS)
def test_is_command_key_matching_keys(command):
    for key in config.keys_for_command(command):
        assert config.is_command_key(command, key)


@pytest.mark.parametrize('command', AVAILABLE_COMMANDS)
def test_is_command_key_nonmatching_keys(command):
    keys_to_test = USED_KEYS - config.keys_for_command(command)
    for key in keys_to_test:
        assert not config.is_command_key(command, key)
