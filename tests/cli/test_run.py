import builtins
import os
import stat
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Tuple

import pytest
import requests
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from zulipterminal.api_types import ServerSettings
from zulipterminal.cli.run import (
    NotAZulipOrganizationError,
    _write_zuliprc,
    exit_with_error,
    get_login_label,
    get_server_settings,
    in_color,
    main,
    parse_args,
)
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.version import ZT_VERSION


MODULE = "zulipterminal.cli.run"
CONTROLLER = MODULE + ".Controller"

os.environ["ZULIP_EDITOR_COMMAND"] = ""


@pytest.mark.parametrize(
    "color, code",
    [
        ("red", "\x1b[91m"),
        ("green", "\x1b[92m"),
        ("yellow", "\x1b[93m"),
        ("blue", "\x1b[94m"),
        ("purple", "\x1b[95m"),
        ("cyan", "\x1b[96m"),
    ],
)
def test_in_color(color: str, code: str, text: str = "some text") -> None:
    assert in_color(color, text) == code + text + "\x1b[0m"


@pytest.mark.parametrize(
    "json, label",
    [
        (
            dict(require_email_format_usernames=False, email_auth_enabled=True),
            "Email or Username",
        ),
        (
            dict(require_email_format_usernames=False, email_auth_enabled=False),
            "Username",
        ),
        (dict(require_email_format_usernames=True, email_auth_enabled=True), "Email"),
        (dict(require_email_format_usernames=True, email_auth_enabled=False), "Email"),
    ],
)
def test_get_login_label(
    mocker: MockerFixture,
    json: ServerSettings,  # NOTE: pytest does not ensure dict above is complete
    label: str,
) -> None:
    result = get_login_label(json)
    assert result == label + ": "


@pytest.fixture
def server_settings_minimal() -> ServerSettings:
    return ServerSettings(
        authentication_methods={},
        external_authentication_methods=[],
        zulip_feature_level=0,  # New in Zulip 3.0, ZFL 1
        zulip_version="2.1.0",
        zulip_merge_base="",  # New in Zulip 5.0, ZFL 88
        push_notifications_enabled=True,
        is_incompatible=False,
        require_email_format_usernames=False,
        email_auth_enabled=True,
        realm_uri="chat.zulip.zulip",  # Present if a Zulip server; preferred URL
        realm_name="A Zulip Server",  # Present if Organization is active at URL
        realm_icon="...",
        realm_description="Very exciting server",
        realm_web_public_access_enabled=True,  # New in Zulip 5.0, ZFL 116
    )


def test_get_server_settings(
    mocker: MockerFixture,
    server_settings_minimal: ServerSettings,
    realm_url: str = "https://chat.zulip.org",
) -> None:
    response = mocker.Mock(
        status_code=requests.codes.OK, json=lambda: server_settings_minimal
    )
    mocked_get = mocker.patch("requests.get", return_value=response)

    result = get_server_settings(realm_url)

    mocked_get.assert_called_once_with(url=realm_url + "/api/v1/server_settings")
    assert result == server_settings_minimal


def test_get_server_settings__not_a_zulip_organization(
    mocker: MockerFixture, realm_url: str = "https://google.com"
) -> None:
    response = mocker.Mock(
        status_code=requests.codes.bad_request  # FIXME: Test others?
    )
    mocked_get = mocker.patch("requests.get", return_value=response)

    with pytest.raises(NotAZulipOrganizationError) as exc:
        get_server_settings(realm_url)

    mocked_get.assert_called_once_with(url=realm_url + "/api/v1/server_settings")
    assert str(exc.value) == realm_url


@pytest.mark.parametrize("options", ["-h", "--help"])
def test_main_help(capsys: CaptureFixture[str], options: str) -> None:
    with pytest.raises(SystemExit):
        main([options])

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")

    assert lines[0].startswith("usage: ")

    required_arguments = {
        "--theme THEME, -t THEME",
        "-h, --help",
        "-d, --debug",
        "--list-themes",
        "--profile",
        "--config-file CONFIG_FILE, -c CONFIG_FILE",
        "--autohide",
        "--no-autohide",
        "-v, --version",
        "-e, --explore",
        "--color-depth",
        "--notify",
        "--no-notify",
        "--transparency",
        "--no-transparency",
    }
    optional_argument_lines = {
        line[2:] for line in lines if len(line) > 2 and line[2] == "-"
    }
    for line in optional_argument_lines:
        assert any(line.startswith(arg) for arg in required_arguments)

    assert captured.err == ""


@pytest.fixture
def platform_mocker(mocker: MockerFixture) -> Callable[[str, str], List[str]]:
    def factory(platform: str, python: str) -> List[str]:
        mocker.patch(MODULE + ".detected_platform", return_value=platform)
        mocker.patch(MODULE + ".detected_python_in_full", return_value=python)
        return ["Detected:", f" - platform: {platform}", f" - python: {python}"]

    return factory


@pytest.fixture
def minimal_zuliprc(tmp_path: Path) -> str:
    zuliprc_path = tmp_path / "zuliprc"
    with open(zuliprc_path, "w") as f:
        f.write("[api]")  # minimal to avoid Exception
    os.chmod(zuliprc_path, 0o600)
    return str(zuliprc_path)


def test_valid_zuliprc_but_no_connection(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    platform_mocker: Callable[[str, str], List[str]],
    minimal_zuliprc: str,
    server_connection_error: str = "some_error",
    platform: str = "some_platform",
    python: str = "3.99 (Zython) [cool]",
) -> None:
    mocker.patch(
        CONTROLLER + ".__init__",
        side_effect=ServerConnectionFailure(server_connection_error),
    )
    expected_platform_output = platform_mocker(platform, python)

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc])

    assert str(e.value) == "1"

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = expected_platform_output + [
        "Loading with:",
        "   theme 'zt_dark' specified from default config.",
        "   autohide setting 'no_autohide' specified from default config.",
        "   exit confirmation setting 'enabled' specified from default config.",
        "   maximum footlinks value '3' specified from default config.",
        "   color depth setting '256' specified from default config.",
        "   notify setting 'disabled' specified from default config.",
        "   transparency setting 'disabled' specified from default config.",
        "   external editor command '' specified from environment.",
        "\x1b[91m",
        f"Error connecting to Zulip server: {server_connection_error}.\x1b[0m",
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize(
    "bad_theme, expected_complete_incomplete_themes, expected_warning",
    [
        ("c", (["a", "b"], ["c", "d"]), "(you could try: a, b)"),
        ("d", ([], ["a", "b", "c", "d"]), "(all themes are incomplete)"),
    ],
)
def test_warning_regarding_incomplete_theme(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    platform_mocker: Callable[[str, str], List[str]],
    minimal_zuliprc: str,
    bad_theme: str,
    expected_complete_incomplete_themes: Tuple[List[str], List[str]],
    expected_warning: str,
    server_connection_error: str = "sce",
    platform: str = "some_platform",
    python: str = "3.99 (Zython) [cool]",
) -> None:
    mocker.patch(
        CONTROLLER + ".__init__",
        side_effect=ServerConnectionFailure(server_connection_error),
    )
    mocker.patch(MODULE + ".detected_platform", return_value=platform)
    mocker.patch(MODULE + ".all_themes", return_value=("a", "b", "c", "d"))
    mocker.patch(
        MODULE + ".complete_and_incomplete_themes",
        return_value=expected_complete_incomplete_themes,
    )
    mocker.patch(MODULE + ".generate_theme")

    expected_platform_output = platform_mocker(platform, python)

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc, "-t", bad_theme])

    assert str(e.value) == "1"

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = expected_platform_output + [
        "Loading with:",
        f"   theme '{bad_theme}' specified on command line.",
        "\x1b[93m   WARNING: Incomplete theme; results may vary!",
        f"      {expected_warning}\x1b[0m",
        "   autohide setting 'no_autohide' specified from default config.",
        "   exit confirmation setting 'enabled' specified from default config.",
        "   maximum footlinks value '3' specified from default config.",
        "   color depth setting '256' specified from default config.",
        "   notify setting 'disabled' specified from default config.",
        "   transparency setting 'disabled' specified from default config.",
        "   external editor command '' specified from environment.",
        "\x1b[91m",
        f"Error connecting to Zulip server: {server_connection_error}.\x1b[0m",
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize("options", ["-v", "--version"])
def test_zt_version(capsys: CaptureFixture[str], options: str) -> None:
    with pytest.raises(SystemExit) as e:
        main([options])

    assert str(e.value) == "0"

    captured = capsys.readouterr()

    lines = captured.out.strip("\n")
    expected = "Zulip Terminal " + ZT_VERSION
    assert lines == expected

    assert captured.err == ""


@pytest.mark.parametrize(
    "option, autohide",
    [
        ("--autohide", "autohide"),
        ("--no-autohide", "no_autohide"),
        ("--debug", None),  # no-autohide by default
    ],
)
def test_parse_args_valid_autohide_option(option: str, autohide: Optional[str]) -> None:
    args = parse_args([option])
    assert args.autohide == autohide


@pytest.mark.parametrize(
    "options", [["--autohide", "--no-autohide"], ["--no-autohide", "--autohide"]]
)
def test_main_multiple_autohide_options(
    capsys: CaptureFixture[str], options: List[str]
) -> None:
    with pytest.raises(SystemExit) as e:
        main(options)

    assert str(e.value) == "2"

    captured = capsys.readouterr()
    expected = f"not allowed with argument {options[0]}"
    assert expected in captured.err


@pytest.mark.parametrize(
    "option, notify_option",
    [
        ("--notify", "enabled"),
        ("--no-notify", "disabled"),
        ("--profile", None),  # disabled by default
    ],
)
def test__parse_args_valid_notify_option(
    option: str, notify_option: Optional[str]
) -> None:
    args = parse_args([option])
    assert args.notify == notify_option


@pytest.mark.parametrize(
    "options",
    [
        ["--notify", "--no-notify"],
        ["--no-notify", "--notify"],
    ],
)
def test_main_multiple_notify_options(
    capsys: CaptureFixture[str], options: List[str]
) -> None:
    with pytest.raises(SystemExit) as e:
        main(options)

    assert str(e.value) == "2"

    captured = capsys.readouterr()
    expected = f"not allowed with argument {options[0]}"
    assert expected in captured.err


# NOTE: Fixture is necessary to ensure unreadable dir is garbage-collected
# See pytest issue #7821
@pytest.fixture
def unreadable_dir(tmp_path: Path) -> Generator[Tuple[Path, Path], None, None]:
    unreadable_dir = tmp_path / "unreadable"
    unreadable_dir.mkdir()
    unreadable_dir.chmod(0)
    if os.access(str(unreadable_dir), os.R_OK):
        # Docker container or similar
        pytest.skip("Directory was still readable")

    yield tmp_path, unreadable_dir

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
    monkeypatch: pytest.MonkeyPatch,
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    unreadable_dir: Tuple[Path, Path],
    path_to_use: str,
    expected_exception: str,
) -> None:
    tmp_path, unusable_path = unreadable_dir

    # This is default base path to use
    zuliprc_path = os.path.join(str(tmp_path), path_to_use)
    monkeypatch.setenv("HOME", zuliprc_path)

    # Give some arbitrary input and fake that it's always valid
    mocker.patch.object(builtins, "input", lambda _: "text\n")
    mocker.patch(
        MODULE + ".get_api_key", return_value=("my_site", "my_login", "my_api_key")
    )

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
def parameterized_zuliprc(tmp_path: Path) -> Callable[[Dict[str, str]], str]:
    def func(config: Dict[str, str]) -> str:
        zuliprc_path = tmp_path / "zuliprc"
        with open(zuliprc_path, "w") as f:
            f.write("[api]\n\n")  # minimal to avoid Exception
            f.write("[zterm]\n")
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        os.chmod(zuliprc_path, 0o600)
        return str(zuliprc_path)

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
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    platform_mocker: Callable[[str, str], List[str]],
    parameterized_zuliprc: Callable[[Dict[str, str]], str],
    config_key: str,
    config_value: str,
    footlinks_output: str,
    platform: str = "some_platform",
    python: str = "3.99 (Zython) [cool]",
) -> None:
    config = {
        "theme": "default",
        "autohide": "autohide",
        "notify": "enabled",
        "color-depth": "256",
    }
    config[config_key] = config_value
    zuliprc = parameterized_zuliprc(config)

    mocker.patch(CONTROLLER + ".__init__", return_value=None)
    mocker.patch(CONTROLLER + ".main", return_value=None)

    expected_platform_output = platform_mocker(platform, python)

    with pytest.raises(SystemExit):
        main(["-c", zuliprc])

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    expected_lines = expected_platform_output + [
        "Loading with:",
        "   theme 'zt_dark' specified in zuliprc file (by alias 'default').",
        "   autohide setting 'autohide' specified in zuliprc file.",
        "   exit confirmation setting 'enabled' specified from default config.",
        f"   maximum footlinks value {footlinks_output}",
        "   color depth setting '256' specified in zuliprc file.",
        "   notify setting 'enabled' specified in zuliprc file.",
        "   transparency setting 'disabled' specified from default config.",
        "   external editor command '' specified from environment.",
    ]
    assert lines == expected_lines


@pytest.mark.parametrize(
    "zulip_config, error_message",
    [
        (
            {"footlinks": "enabled", "maximum-footlinks": "3"},
            "Configuration Error: footlinks and maximum-footlinks options"
            " cannot be used together",
        ),
        (
            {"maximum-footlinks": "-3"},
            "Configuration Error: Minimum value allowed for maximum-footlinks"
            " is 0; you used '-3'",
        ),
    ],
)
def test_main_error_with_invalid_zuliprc_options(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    platform_mocker: Callable[[str, str], List[str]],
    parameterized_zuliprc: Callable[[Dict[str, str]], str],
    zulip_config: Dict[str, str],
    error_message: str,
    platform: str = "some_platform",
    python: str = "3.99 (Zython) [cool]",
) -> None:
    zuliprc = parameterized_zuliprc(zulip_config)
    mocker.patch(CONTROLLER + ".__init__", return_value=None)
    mocker.patch(MODULE + ".detected_platform", return_value=platform)
    mocker.patch(CONTROLLER + ".main", return_value=None)

    expected_platform_output = platform_mocker(platform, python)

    with pytest.raises(SystemExit) as e:
        main(["-c", zuliprc])

    assert str(e.value) == "1"

    captured = capsys.readouterr()
    lines = captured.out.strip()
    expected_lines = "\n".join(
        expected_platform_output + [f"\033[91m{error_message}\033[0m"]
    )
    assert lines == expected_lines


@pytest.mark.parametrize(
    "error_code, helper_text",
    [
        (1, ""),
        (2, "helper"),
    ],
)
def test_exit_with_error(
    capsys: CaptureFixture[str],
    error_code: int,
    helper_text: str,
    error_message: str = "some text",
) -> None:
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


def test__write_zuliprc__success(
    tmp_path: Path, id: str = "id", key: str = "key", url: str = "url"
) -> None:
    path = os.path.join(str(tmp_path), "zuliprc")

    error_message = _write_zuliprc(path, api_key=key, server_url=url, login_id=id)

    assert error_message == ""

    expected_contents = f"[api]\nemail={id}\nkey={key}\nsite={url}"
    with open(path) as f:
        assert f.read() == expected_contents

    assert stat.filemode(os.stat(path).st_mode)[-6:] == 6 * "-"


def test__write_zuliprc__fail_file_exists(
    minimal_zuliprc: str,
    tmp_path: Path,
    id: str = "id",
    key: str = "key",
    url: str = "url",
) -> None:
    path = os.path.join(str(tmp_path), "zuliprc")

    error_message = _write_zuliprc(path, api_key=key, server_url=url, login_id=id)

    assert error_message == "zuliprc already exists at " + path


@pytest.mark.parametrize(
    "mode",
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
    capsys: CaptureFixture[str], minimal_zuliprc: str, mode: int
) -> None:
    mode += 0o600
    os.chmod(minimal_zuliprc, mode)
    current_mode = stat.filemode(os.stat(minimal_zuliprc).st_mode)

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc])

    assert str(e.value) == "1"

    captured = capsys.readouterr()

    lines = captured.out.split("\n")[:-1]
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
