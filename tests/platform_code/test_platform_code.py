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
    "PLATFORM, is_notification_sent",
    [
        # PLATFORM: Literal["WSL", "MacOS", "Linux", "unsupported"]
        pytest.param(
            "WSL",
            True,
            marks=pytest.mark.xfail(reason="WSL notify disabled"),
        ),
        ("MacOS", True),
        ("Linux", True),
        ("unsupported", False),  # Unsupported OS
    ],
)
def test_notify(
    mocker: MockerFixture, PLATFORM: AllPlatforms, is_notification_sent: bool
) -> None:
    title = "Author"
    text = "Hello!"
    mocker.patch(MODULE + ".PLATFORM", PLATFORM)
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
    "PLATFORM, cmd_length",
    [
        ("Linux", 4),
        ("MacOS", 10),
        pytest.param("WSL", 2, marks=pytest.mark.xfail(reason="WSL notify disabled")),
    ],
)
def test_notify_quotes(
    mocker: MockerFixture,
    PLATFORM: SupportedPlatforms,
    cmd_length: int,
    title: str,
    text: str,
) -> None:
    subprocess = mocker.patch(MODULE + ".subprocess")
    mocker.patch(MODULE + ".PLATFORM", PLATFORM)

    notify(title, text)

    params = subprocess.run.call_args_list
    assert len(params) == 1  # One external run call
    assert len(params[0][0][0]) == cmd_length

    # NOTE: If there is a quoting error, we may get a ValueError too


@pytest.mark.parametrize(
    "PLATFORM, expected_return_code",
    [
        ("Linux", 0),
        ("MacOS", 0),
        ("WSL", 1),
    ],
)
def test_successful_GUI_return_code(
    mocker: MockerFixture,
    PLATFORM: SupportedPlatforms,
    expected_return_code: int,
) -> None:
    mocker.patch(MODULE + ".PLATFORM", PLATFORM)
    assert successful_GUI_return_code() == expected_return_code


@pytest.mark.parametrize(
    "PLATFORM, expected_path",
    [
        ("Linux", "/path/to/file"),
        ("MacOS", "/path/to/file"),
        ("WSL", "\\path\\to\\file"),
    ],
)
def test_normalized_file_path(
    mocker: MockerFixture,
    PLATFORM: SupportedPlatforms,
    expected_path: str,
    path: str = "/path/to/file",
) -> None:
    mocker.patch(MODULE + ".PLATFORM", PLATFORM)
    assert normalized_file_path(path) == expected_path
