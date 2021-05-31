import builtins
import os
import stat

import pytest

from zulipterminal.cli.run import (
    THEMES,
    _write_zuliprc,
    exit_with_error,
    get_login_id,
    in_color,
    main,
    parse_args,
)
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.version import ZT_VERSION


@pytest.mark.parametrize(
    'color, code',
    [
        ('red', '\x1b[91m'),
        ('green', '\x1b[92m'),
        ('yellow', '\x1b[93m'),
        ('blue', '\x1b[94m'),
        ('purple', '\x1b[95m'),
        ('cyan', '\x1b[96m'),
    ],
)
def test_in_color(color, code, text="some text"):
    assert in_color(color, text) == code + text + "\x1b[0m"


@pytest.mark.parametrize(
    'json, label',
    [
        (
            dict(require_email_format_usernames=False, email_auth_enabled=True),
            'Email or Username',
        ),
        (
            dict(require_email_format_usernames=False, email_auth_enabled=False),
            'Username',
        ),
        (dict(require_email_format_usernames=True, email_auth_enabled=True), 'Email'),
        (dict(require_email_format_usernames=True, email_auth_enabled=False), 'Email'),
    ],
)
def test_get_login_id(mocker, json, label):
    response = mocker.Mock(json=lambda: json)
    mocked_get = mocker.patch('requests.get', return_value=response)
    mocked_styled_input = mocker.patch(
        'zulipterminal.cli.run.styled_input', return_value='input return value'
    )

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
        '--list-themes',
        '--profile',
        '--config-file CONFIG_FILE, -c CONFIG_FILE',
        '--autohide',
        '--no-autohide',
        '-v, --version',
        '-e, --explore',
        '--color-depth',
        '--notify',
        '--no-notify',
    }
    optional_argument_lines = {
        line[2:] for line in lines if len(line) > 2 and line[2] == '-'
    }
    for line in optional_argument_lines:
        assert any(line.startswith(arg) for arg in required_arguments)

    assert captured.err == ""


@pytest.fixture
def minimal_zuliprc(tmpdir):
    zuliprc_path = str(tmpdir) + "/zuliprc"
    with open(zuliprc_path, "w") as f:
        f.write("[api]")  # minimal to avoid Exception
    os.chmod(zuliprc_path, 0o600)
    return zuliprc_path


def test_valid_zuliprc_but_no_connection(
    capsys, mocker, minimal_zuliprc, server_connection_error="some_error"
):
    mocker.patch(
        'zulipterminal.core.Controller.__init__',
        side_effect=ServerConnectionFailure(server_connection_error),
    )

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc])

    assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        "Loading with:",
        "   theme 'zt_dark' specified with no config.",
        "   autohide setting 'no_autohide' specified with no config.",
        "   maximum footlinks value '3' specified with no config.",
        "   color depth setting '256' specified with no config.",
        "   notify setting 'disabled' specified with no config.",
        "\x1b[91m",
        f"Error connecting to Zulip server: {server_connection_error}.\x1b[0m",
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize('bad_theme', ['c', 'd'])
def test_warning_regarding_incomplete_theme(
    capsys,
    mocker,
    monkeypatch,
    minimal_zuliprc,
    bad_theme,
    server_connection_error="sce",
):
    mocker.patch(
        'zulipterminal.core.Controller.__init__',
        side_effect=ServerConnectionFailure(server_connection_error),
    )

    monkeypatch.setitem(THEMES, bad_theme, [])
    mocker.patch('zulipterminal.cli.run.all_themes', return_value=('a', 'b', 'c', 'd'))
    mocker.patch(
        'zulipterminal.cli.run.complete_and_incomplete_themes',
        return_value=(['a', 'b'], ['c', 'd']),
    )

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc, "-t", bad_theme])

    assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        "Loading with:",
        f"   theme '{bad_theme}' specified on command line.",
        "\x1b[93m   WARNING: Incomplete theme; results may vary!",
        f"      (you could try: {'a'}, {'b'})\x1b[0m",
        "   autohide setting 'no_autohide' specified with no config.",
        "   maximum footlinks value '3' specified with no config.",
        "   color depth setting '256' specified with no config.",
        "   notify setting 'disabled' specified with no config.",
        "\x1b[91m",
        f"Error connecting to Zulip server: {server_connection_error}.\x1b[0m",
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


@pytest.mark.parametrize(
    'option, autohide',
    [
        ('--autohide', 'autohide'),
        ('--no-autohide', 'no_autohide'),
        ('--debug', None),  # no-autohide by default
    ],
)
def test_parse_args_valid_autohide_option(option, autohide):
    args = parse_args([option])
    assert args.autohide == autohide


@pytest.mark.parametrize(
    'options', [['--autohide', '--no-autohide'], ['--no-autohide', '--autohide']]
)
def test_main_multiple_autohide_options(capsys, options):
    with pytest.raises(SystemExit) as e:
        main(options)

    assert str(e.value) == "2"

    captured = capsys.readouterr()
    lines = captured.err.strip('\n')
    lines = lines.split("pytest: ", 1)[1]
    expected = f"error: argument {options[1]}: not allowed with argument {options[0]}"
    assert lines == expected


@pytest.mark.parametrize(
    'option, notify_option',
    [
        ('--notify', 'enabled'),
        ('--no-notify', 'disabled'),
        ('--profile', None),  # disabled by default
    ],
)
def test__parse_args_valid_notify_option(option, notify_option):
    args = parse_args([option])
    assert args.notify == notify_option


@pytest.mark.parametrize(
    'options',
    [
        ['--notify', '--no-notify'],
        ['--no-notify', '--notify'],
    ],
)
def test_main_multiple_notify_options(capsys, options):
    with pytest.raises(SystemExit) as e:
        main(options)

    assert str(e.value) == "2"

    captured = capsys.readouterr()
    lines = captured.err.strip('\n')
    lines = lines.split("pytest: ", 1)[1]
    expected = f"error: argument {options[1]}: not allowed with argument {options[0]}"
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


@pytest.mark.parametrize(
    "path_to_use, expected_exception",
    [
        ("unreadable", "PermissionError"),
        ("goodnewhome", "FileNotFoundError"),
    ],
    ids=["valid_path_but_cannot_be_written_to", "path_does_not_exist"],
)
def test_main_cannot_write_zuliprc_given_good_credentials(
    monkeypatch,
    capsys,
    mocker,
    unreadable_dir,
    path_to_use,
    expected_exception,
):
    tmpdir, unusable_path = unreadable_dir

    # This is default base path to use
    zuliprc_path = os.path.join(str(tmpdir), path_to_use)
    monkeypatch.setenv("HOME", zuliprc_path)

    # Give some arbitrary input and fake that it's always valid
    mocker.patch.object(builtins, 'input', lambda _: 'text\n')
    response = mocker.Mock(json=lambda: dict(api_key=""), status_code=200)
    mocker.patch("zulipterminal.cli.run.get_api_key", return_value=(response, None))

    with pytest.raises(SystemExit):
        main([])

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    expected_line = (
        "\x1b[91m"
        f"{expected_exception}: zuliprc could not be created "
        f"at {os.path.join(zuliprc_path, 'zuliprc')}"
        "\x1b[0m"
    )
    assert lines[-1] == expected_line


@pytest.fixture
def parameterized_zuliprc(tmpdir):
    def func(config):
        zuliprc_path = str(tmpdir) + "/zuliprc"
        with open(zuliprc_path, "w") as f:
            f.write("[api]\n\n")  # minimal to avoid Exception
            f.write("[zterm]\n")
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        os.chmod(zuliprc_path, 0o600)
        return zuliprc_path

    return func


@pytest.mark.parametrize(
    "config_key, config_value, footlinks_output",
    [
        ("footlinks", "disabled", "'0' specified in zuliprc file from footlinks."),
        ("footlinks", "enabled", "'3' specified in zuliprc file from footlinks."),
        ("maximum-footlinks", "3", "'3' specified in zuliprc file."),
        ("maximum-footlinks", "0", "'0' specified in zuliprc file."),
    ],
    ids=[
        "footlinks_disabled",
        "footlinks_enabled",
        "maximum-footlinks_3",
        "maximum-footlinks_0",
    ],
)
def test_successful_main_function_with_config(
    capsys,
    mocker,
    parameterized_zuliprc,
    config_key,
    config_value,
    footlinks_output,
):
    config = {
        "theme": "default",
        "autohide": "autohide",
        "notify": "enabled",
        "color-depth": "256",
    }
    config[config_key] = config_value
    zuliprc = parameterized_zuliprc(config)
    mocker.patch("zulipterminal.core.Controller.__init__", return_value=None)
    mocker.patch("zulipterminal.core.Controller.main", return_value=None)

    with pytest.raises(SystemExit):
        main(["-c", zuliprc])

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    expected_lines = [
        'Loading with:',
        "   theme 'zt_dark' specified in zuliprc file (by alias 'default').",
        "   autohide setting 'autohide' specified in zuliprc file.",
        f"   maximum footlinks value {footlinks_output}",
        "   color depth setting '256' specified in zuliprc file.",
        "   notify setting 'enabled' specified in zuliprc file.",
    ]
    assert lines == expected_lines


@pytest.mark.parametrize(
    "zulip_config, error_message",
    [
        (
            {"footlinks": "enabled", "maximum-footlinks": "3"},
            "Footlinks property is not allowed alongside maximum-footlinks",
        ),
        (
            {"maximum-footlinks": "-3"},
            "Minimum value allowed for maximum-footlinks is 0",
        ),
    ],
)
def test_main_error_with_invalid_zuliprc_options(
    capsys,
    mocker,
    parameterized_zuliprc,
    zulip_config,
    error_message,
):
    zuliprc = parameterized_zuliprc(zulip_config)
    mocker.patch("zulipterminal.core.Controller.__init__", return_value=None)
    mocker.patch("zulipterminal.core.Controller.main", return_value=None)

    with pytest.raises(SystemExit) as e:
        main(["-c", zuliprc])

    assert str(e.value) == "1"

    captured = capsys.readouterr()
    lines = captured.out.strip()
    expected_lines = f"\033[91m{error_message}\033[0m"
    assert lines == expected_lines


@pytest.mark.parametrize(
    'error_code, helper_text',
    [
        (1, ""),
        (2, "helper"),
    ],
)
def test_exit_with_error(error_code, helper_text, capsys, error_message="some text"):
    with pytest.raises(SystemExit) as e:
        exit_with_error(
            error_message=error_message, helper_text=helper_text, error_code=error_code
        )

    assert str(e.value) == str(error_code)

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    expected_line = f"\033[91m{error_message}\033[0m"
    assert lines[0] == expected_line

    if helper_text:
        assert lines[1] == helper_text


def test__write_zuliprc__success(tmpdir, id="id", key="key", url="url"):
    path = os.path.join(str(tmpdir), "zuliprc")

    error_message = _write_zuliprc(path, api_key=key, server_url=url, login_id=id)

    assert error_message == ""

    expected_contents = f"[api]\nemail={id}\nkey={key}\nsite={url}"
    with open(path) as f:
        assert f.read() == expected_contents

    assert stat.filemode(os.stat(path).st_mode)[-6:] == 6 * "-"


def test__write_zuliprc__fail_file_exists(
    minimal_zuliprc, tmpdir, id="id", key="key", url="url"
):
    path = os.path.join(str(tmpdir), "zuliprc")

    error_message = _write_zuliprc(path, api_key=key, server_url=url, login_id=id)

    assert error_message == "zuliprc already exists at " + path


@pytest.mark.parametrize(
    'mode',
    [
        # Avoid reformatting to retain readability of grid of values
        # fmt:off
        0o77, 0o70, 0o07,
        0o66, 0o60, 0o06,
        0o55, 0o50, 0o05,
        0o44, 0o40, 0o04,
        0o33, 0o30, 0o03,
        0o22, 0o20, 0o02,
        0o11, 0o10, 0o01,
        # fmt:on
    ],
)
def test_show_error_if_loading_zuliprc_with_open_permissions(
    capsys, minimal_zuliprc, mode
):
    mode += 0o600
    os.chmod(minimal_zuliprc, mode)
    current_mode = stat.filemode(os.stat(minimal_zuliprc).st_mode)

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc])

    assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.split('\n')[:-1]
    expected_last_lines = [
        f"(it currently has permissions '{current_mode}')",
        "This can often be achieved with a command such as:",
        f"  chmod og-rwx {minimal_zuliprc}",
        "Consider regenerating the [api] part of your zuliprc to ensure "
        "your account is secure."
        "\x1b[0m",
    ]
    assert lines[-4:] == expected_last_lines

    assert captured.err == ""
