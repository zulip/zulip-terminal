from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture

from zulipterminal.config import keys


AVAILABLE_COMMANDS = list(keys.KEY_BINDINGS.keys())

USED_KEYS = {key for values in keys.KEY_BINDINGS.values() for key in values["keys"]}


@pytest.fixture(params=keys.KEY_BINDINGS.keys())
def valid_command(request: Any) -> str:
    return request.param


@pytest.fixture(params=["BLAH*10"])
def invalid_command(request: Any) -> str:
    return request.param


def test_keys_for_command(valid_command: str) -> None:
    assert keys.KEY_BINDINGS[valid_command]["keys"] == keys.keys_for_command(
        valid_command
    )


def test_primary_key_for_command(valid_command: str) -> None:
    assert keys.KEY_BINDINGS[valid_command]["keys"][0] == keys.primary_key_for_command(
        valid_command
    )


def test_keys_for_command_invalid_command(invalid_command: str) -> None:
    with pytest.raises(keys.InvalidCommand):
        keys.keys_for_command(invalid_command)


def test_keys_for_command_identity(valid_command: str) -> None:
    """
    Ensures that each call to keys_for_command returns the original keys in a
    new list which validates that the original keys don't get altered
    elsewhere unintentionally.
    """
    assert id(keys.KEY_BINDINGS[valid_command]["keys"]) != id(
        keys.keys_for_command(valid_command)
    )


def test_is_command_key_matching_keys(valid_command: str) -> None:
    for key in keys.keys_for_command(valid_command):
        assert keys.is_command_key(valid_command, key)


def test_is_command_key_nonmatching_keys(valid_command: str) -> None:
    keys_to_test = USED_KEYS - set(keys.keys_for_command(valid_command))
    for key in keys_to_test:
        assert not keys.is_command_key(valid_command, key)


def test_is_command_key_invalid_command(invalid_command: str) -> None:
    with pytest.raises(keys.InvalidCommand):
        keys.is_command_key(invalid_command, "esc")  # key doesn't matter


def test_HELP_is_not_allowed_as_tip() -> None:
    assert keys.KEY_BINDINGS["HELP"]["excluded_from_random_tips"] is True
    assert keys.KEY_BINDINGS["HELP"] not in keys.commands_for_random_tips()


def test_commands_for_random_tips(mocker: MockerFixture) -> None:
    new_key_bindings: Dict[str, keys.KeyBinding] = {
        "ALPHA": {
            "keys": ["a"],
            "help_text": "alpha",
            "key_category": "category 1",
            "excluded_from_random_tips": True,
        },
        "BETA": {
            "keys": ["b"],
            "help_text": "beta",
            "key_category": "category 1",
            "excluded_from_random_tips": False,
        },
        "GAMMA": {
            "keys": ["g"],
            "help_text": "gamma",
            "key_category": "category 1",
        },
        "DELTA": {
            "keys": ["d"],
            "help_text": "delta",
            "key_category": "category 2",
            "excluded_from_random_tips": True,
        },
    }
    mocker.patch.dict(keys.KEY_BINDINGS, new_key_bindings, clear=True)
    result = keys.commands_for_random_tips()
    assert len(result) == 2
    assert new_key_bindings["BETA"] in result
    assert new_key_bindings["GAMMA"] in result


def test_updated_urwid_command_map() -> None:
    urwid_to_zt_mapping = {v: k for k, v in keys.ZT_TO_URWID_CMD_MAPPING.items()}
    # Check if keys in command map are actually the ones in KEY_BINDINGS
    for key, urwid_cmd in keys.command_map._command.items():
        try:
            zt_cmd = urwid_to_zt_mapping[urwid_cmd]
            assert key in keys.keys_for_command(zt_cmd)
        except KeyError:
            pass


@pytest.mark.parametrize(
    "urwid_key, display_key",
    [
        ("a", "a"),
        ("B", "B"),
        (":", ":"),
        ("enter", "Enter"),
        ("meta c", "Meta c"),
        ("ctrl D", "Ctrl D"),
        ("page up", "PgUp"),
        ("ctrl page up", "Ctrl PgUp"),
    ],
    ids=[
        "lowercase_alphabet_key",
        "uppercase_alphabet_key",
        "symbol_key",
        "special_key",
        "lowercase_alphabet_key_with_modifier_key",
        "uppercase_alphabet_key_with_modifier_key",
        "mapped_key",
        "mapped_key_with_modifier_key",
    ],
)
def test_display_key_for_urwid_key(urwid_key: str, display_key: str) -> None:
    assert keys.display_key_for_urwid_key(urwid_key) == display_key


COMMAND_TO_DISPLAY_KEYS = [
    ("NEXT_LINE", ["Down", "Ctrl n"]),
    ("TOGGLE_STAR_STATUS", ["Ctrl s", "*"]),
    ("ALL_DM", ["P"]),
]


@pytest.mark.parametrize("command, display_keys", COMMAND_TO_DISPLAY_KEYS)
def test_display_keys_for_command(command: str, display_keys: List[str]) -> None:
    assert keys.display_keys_for_command(command) == display_keys


@pytest.mark.parametrize("command, display_keys", COMMAND_TO_DISPLAY_KEYS)
def test_primary_display_key_for_command(command: str, display_keys: List[str]) -> None:
    assert keys.primary_display_key_for_command(command) == display_keys[0]


def test_display_keys_for_command_invalid_command(invalid_command: str) -> None:
    with pytest.raises(keys.InvalidCommand):
        keys.display_keys_for_command(invalid_command)
