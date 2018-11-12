import pytest

from zulipterminal import config

AVAILABLE_COMMANDS = list(config.KEY_BINDINGS.keys())

USED_KEYS = {key
             for values in config.KEY_BINDINGS.values()
             for key in values['keys']}


@pytest.fixture(params=config.KEY_BINDINGS.keys())
def valid_command(request):
    return request.param


@pytest.fixture(params=['BLAH*10'])
def invalid_command(request):
    return request.param


def test_keys_for_command(valid_command):
    assert (config.KEY_BINDINGS[valid_command]['keys'] ==
            config.keys_for_command(valid_command))


def test_keys_for_command_invalid_command(invalid_command):
    with pytest.raises(config.InvalidCommand):
        config.keys_for_command(invalid_command)


def test_is_command_key_matching_keys(valid_command):
    for key in config.keys_for_command(valid_command):
        assert config.is_command_key(valid_command, key)


def test_is_command_key_nonmatching_keys(valid_command):
    keys_to_test = USED_KEYS - config.keys_for_command(valid_command)
    for key in keys_to_test:
        assert not config.is_command_key(valid_command, key)


def test_is_command_key_invalid_command(invalid_command):
    with pytest.raises(config.InvalidCommand):
        config.is_command_key(invalid_command, 'esc')  # key doesn't matter
