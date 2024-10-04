import pytest
from pytest_mock import MockerFixture

from zulipterminal.platform_code import (
    AllPlatforms,
    SupportedPlatforms,
    normalized_file_path,
    notify,
    successful_GUI_return_code,
)


MODULE = "zulipterminal.platform_code"


@pytest.mark.parametrize(
    "platform, is_notification_sent",
    [
        # platform: Literal["WSL", "MacOS", "Linux", "Unsupported"]
        pytest.param(
            "WSL",
            True,
            marks=pytest.mark.xfail(reason="WSL notify disabled"),
        ),
        ("MacOS", True),
        ("Linux", True),
        ("Unsupported", False),  # Unsupported OS
    ],
)
def test_notify(
    mocker: MockerFixture, platform: AllPlatforms, is_notification_sent: bool
) -> None:
    title = "Author"
    text = "Hello!"
    mocker.patch(MODULE + ".PLATFORM", platform)
    subprocess = mocker.patch(MODULE + ".subprocess")
    notify(title, text)
    assert subprocess.run.called == is_notification_sent


@pytest.mark.parametrize(
    "text",
    ["x", "Spaced text.", "'", '"'],
    ids=["x", "spaced_text", "single", "double"],
)
@pytest.mark.parametrize(
    "title",
    ["X", "Spaced title", "'", '"'],
    ids=["X", "spaced_title", "single", "double"],
)
@pytest.mark.parametrize(
    "platform, cmd_length",
    [
        ("Linux", 4),
        ("MacOS", 10),
        pytest.param("WSL", 2, marks=pytest.mark.xfail(reason="WSL notify disabled")),
    ],
)
def test_notify_quotes(
    mocker: MockerFixture,
    platform: SupportedPlatforms,
    cmd_length: int,
    title: str,
    text: str,
) -> None:
    subprocess = mocker.patch(MODULE + ".subprocess")
    mocker.patch(MODULE + ".PLATFORM", platform)

    notify(title, text)

    params = subprocess.run.call_args_list
    assert len(params) == 1  # One external run call
    assert len(params[0][0][0]) == cmd_length

    # NOTE: If there is a quoting error, we may get a ValueError too


@pytest.mark.parametrize(
    "platform, expected_return_code",
    [
        ("Linux", 0),
        ("MacOS", 0),
        ("WSL", 1),
    ],
)
def test_successful_GUI_return_code(
    mocker: MockerFixture,
    platform: SupportedPlatforms,
    expected_return_code: int,
) -> None:
    mocker.patch(MODULE + ".PLATFORM", platform)
    assert successful_GUI_return_code() == expected_return_code


@pytest.mark.parametrize(
    "platform, expected_path",
    [
        ("Linux", "/path/to/file"),
        ("MacOS", "/path/to/file"),
        ("WSL", "\\path\\to\\file"),
    ],
)
def test_normalized_file_path(
    mocker: MockerFixture,
    platform: SupportedPlatforms,
    expected_path: str,
    path: str = "/path/to/file",
) -> None:
    mocker.patch(MODULE + ".PLATFORM", platform)
    assert normalized_file_path(path) == expected_path
