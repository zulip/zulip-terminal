import pytest

from zulipterminal.config import keys

AVAILABLE_COMMANDS = list(keys.KEY_BINDINGS.keys())

USED_KEYS = {key
             for values in keys.KEY_BINDINGS.values()
             for key in values['keys']}


@pytest.fixture(params=keys.KEY_BINDINGS.keys())
def valid_command(request):
    return request.param


@pytest.fixture(params=['BLAH*10'])
def invalid_command(request):
    return request.param


def test_keys_for_command(valid_command):
    assert (keys.KEY_BINDINGS[valid_command]['keys'] ==
            keys.keys_for_command(valid_command))


def test_keys_for_command_invalid_command(invalid_command):
    with pytest.raises(keys.InvalidCommand):
        keys.keys_for_command(invalid_command)


def test_is_command_key_matching_keys(valid_command):
    for key in keys.keys_for_command(valid_command):
        assert keys.is_command_key(valid_command, key)


def test_is_command_key_nonmatching_keys(valid_command):
    keys_to_test = USED_KEYS - keys.keys_for_command(valid_command)
    for key in keys_to_test:
        assert not keys.is_command_key(valid_command, key)


def test_is_command_key_invalid_command(invalid_command):
    with pytest.raises(keys.InvalidCommand):
        keys.is_command_key(invalid_command, 'esc')  # key doesn't matter


def test_HELP_is_not_allowed_as_tip():
    assert (keys.KEY_BINDINGS['HELP']['excluded_from_random_tips'] is True)
    assert (keys.KEY_BINDINGS['HELP'] not in keys.commands_for_random_tips())


def test_commands_for_random_tips(mocker):
    new_key_bindings = {
        'ALPHA': {
            'keys': {'a'},
            'help_text': 'alpha',
            'excluded_from_random_tips': True,
            },
        'BETA': {
            'keys': {'b'},
            'help_text': 'beta',
            'excluded_from_random_tips': False,
            },
        'GAMMA': {
            'keys': {'g'},
            'help_text': 'gamma',
            },
        'DELTA': {
            'keys': {'d'},
            'help_text': 'delta',
            'excluded_from_random_tips': True,
            },
    }  # type: Dict[str, KeyBinding]
    mocker.patch.dict(keys.KEY_BINDINGS, new_key_bindings, clear=True)
    result = keys.commands_for_random_tips()
    assert len(result) == 2
    assert new_key_bindings['BETA'] in result
    assert new_key_bindings['GAMMA'] in result
