import pytest
from pytest_mock import MockerFixture

from zulipterminal.platform_code import AllPlatforms, SupportedPlatforms, notify


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
    platform = mocker.patch(MODULE + ".PLATFORM", PLATFORM)

    notify(title, text)

    params = subprocess.run.call_args_list
    assert len(params) == 1  # One external run call
    assert len(params[0][0][0]) == cmd_length

    # NOTE: If there is a quoting error, we may get a ValueError too
