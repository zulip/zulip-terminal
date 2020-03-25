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
        '-v, --version'
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
