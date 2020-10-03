import builtins
import os

import pytest

from zulipterminal.cli.run import (
    THEMES, get_login_id, in_color, main, parse_args,
)
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.version import ZT_VERSION


@pytest.mark.parametrize('color, code', [
    ('red', '\x1b[91m'),
    ('green', '\x1b[92m'),
    ('yellow', '\x1b[93m'),
    ('blue', '\x1b[94m'),
    ('purple', '\x1b[95m'),
    ('cyan', '\x1b[96m'),
])
def test_in_color(color, code, text="some text"):
    assert in_color(color, text) == code + text + "\x1b[0m"


@pytest.mark.parametrize('json, label', [
    (dict(require_email_format_usernames=False, email_auth_enabled=True),
     'Email or Username'),
    (dict(require_email_format_usernames=False, email_auth_enabled=False),
     'Username'),
    (dict(require_email_format_usernames=True, email_auth_enabled=True),
     'Email'),
    (dict(require_email_format_usernames=True, email_auth_enabled=False),
     'Email'),
])
def test_get_login_id(mocker, json, label):
    response = mocker.Mock(json=lambda: json)
    mocked_get = mocker.patch('requests.get', return_value=response)
    mocked_styled_input = mocker.patch('zulipterminal.cli.run.styled_input',
                                       return_value='input return value')

    result = get_login_id('REALM_URL')

    assert result == 'input return value'
    mocked_get.assert_called_with(url='REALM_URL/api/v1/server_settings')
    mocked_styled_input.assert_called_with(label + ': ')


@pytest.mark.parametrize('options', ['-h', '--help'])
def test_main_help(capsys, options):
    with pytest.raises(SystemExit):
        main([options])

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")

    assert lines[0].startswith('usage: ')

    required_arguments = {
        '--theme THEME, -t THEME',
        '-h, --help',
        '-d, --debug',
        '--profile',
        '--config-file CONFIG_FILE, -c CONFIG_FILE',
        '--autohide',
        '--no-autohide',
        '-v, --version',
        '-e, --explore',
        '--color-depth'
    }
    optional_argument_lines = {line[2:] for line in lines
                               if len(line) > 2 and line[2] == '-'}
    for line in optional_argument_lines:
        assert any(line.startswith(arg) for arg in required_arguments)

    assert captured.err == ""


@pytest.fixture
def minimal_zuliprc(tmpdir):
    zuliprc_path = str(tmpdir) + "/zuliprc"
    with open(zuliprc_path, "w") as f:
        f.write("[api]")  # minimal to avoid Exception
    return zuliprc_path


def test_valid_zuliprc_but_no_connection(capsys, mocker, minimal_zuliprc,
                                         server_connection_error="some_error"):
    mocker.patch('zulipterminal.core.Controller.__init__',
                 side_effect=ServerConnectionFailure(server_connection_error))

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc])
        assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        "Loading with:",
        "   theme 'zt_dark' specified with no config.",
        "   autohide setting 'no_autohide' specified with no config.",
        "   footlinks setting 'enabled' specified with no config.",
        "\x1b[91m",
        ("Error connecting to Zulip server: {}.\x1b[0m".
            format(server_connection_error)),
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize('bad_theme', ['c', 'd'])
def test_warning_regarding_incomplete_theme(capsys, mocker, monkeypatch,
                                            minimal_zuliprc, bad_theme,
                                            server_connection_error="sce"):
    mocker.patch('zulipterminal.core.Controller.__init__',
                 side_effect=ServerConnectionFailure(server_connection_error))

    monkeypatch.setitem(THEMES, bad_theme, [])
    mocker.patch('zulipterminal.cli.run.all_themes',
                 return_value=('a', 'b', 'c', 'd'))
    mocker.patch('zulipterminal.cli.run.complete_and_incomplete_themes',
                 return_value=(['a', 'b'], ['c', 'd']))

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc, "-t", bad_theme])
        assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        "Loading with:",
        "   theme '{}' specified on command line.".format(bad_theme),
        "\x1b[93m"
        "   WARNING: Incomplete theme; results may vary!",
        "      (you could try: {}, {})"
        "\x1b[0m".format('a', 'b'),
        "   autohide setting 'no_autohide' specified with no config.",
        "   footlinks setting 'enabled' specified with no config.",
        "\x1b[91m",
        ("Error connecting to Zulip server: {}.\x1b[0m".
            format(server_connection_error)),
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize('options', ['-v', '--version'])
def test_zt_version(capsys, options):
    with pytest.raises(SystemExit) as e:
        main([options])
        assert str(e.value) == "0"

    captured = capsys.readouterr()

    lines = captured.out.strip('\n')
    expected = 'Zulip Terminal ' + ZT_VERSION
    assert lines == expected

    assert captured.err == ""


@pytest.mark.parametrize('option, autohide', [
        ('--autohide', 'autohide'),
        ('--no-autohide', 'no_autohide'),
        ('--debug', None),  # no-autohide by default
])
def test_parse_args_valid_autohide_option(option, autohide):
    args = parse_args([option])
    assert args.autohide == autohide


@pytest.mark.parametrize('options', [
        ['--autohide', '--no-autohide'],
        ['--no-autohide', '--autohide']
])
def test_main_multiple_autohide_options(capsys, options):
    with pytest.raises(SystemExit) as e:
        main(options)
        assert str(e.value) == "2"
    captured = capsys.readouterr()
    lines = captured.err.strip('\n')
    lines = lines.split("pytest: ", 1)[1]
    expected = ("error: argument {}: not allowed "
                "with argument {}".format(options[1], options[0]))
    assert lines == expected


# NOTE: Fixture is necessary to ensure unreadable dir is garbage-collected
# See pytest issue #7821
@pytest.fixture
def unreadable_dir(tmpdir):
    unreadable_dir = tmpdir.mkdir("unreadable")
    unreadable_dir.chmod(0)
    if os.access(str(unreadable_dir), os.R_OK):
        # Docker container or similar
        pytest.skip("Directory was still readable")

    yield tmpdir, unreadable_dir

    unreadable_dir.chmod(0o755)


@pytest.mark.parametrize("path_to_use, expected_exception", [
    ("unreadable", "PermissionError"),
    ("goodnewhome", "FileNotFoundError"),
], ids=[
    "valid_path_but_cannot_be_written_to",
    "path_does_not_exist"
])
def test_main_cannot_write_zuliprc_given_good_credentials(
    monkeypatch, capsys, mocker,
    unreadable_dir,
    path_to_use, expected_exception,
):
    tmpdir, unusable_path = unreadable_dir

    # This is default base path to use
    zuliprc_path = os.path.join(str(tmpdir), path_to_use)
    monkeypatch.setenv("HOME", zuliprc_path)

    # Give some arbitrary input and fake that it's always valid
    mocker.patch.object(builtins, 'input', lambda _: 'text\n')
    mocker.patch("zulipterminal.cli.run.get_api_key",
                 return_value=(mocker.Mock(status_code=200), None))

    with pytest.raises(SystemExit):
        main([])

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    expected_line = (
        "\x1b[91m"
        "{}: zuliprc could not be created at {}"
        "\x1b[0m"
        .format(
            expected_exception,
            os.path.join(zuliprc_path, "zuliprc")
        )
    )
    assert lines[-1] == expected_line
