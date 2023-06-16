"""
Detection of supported platforms & platform-specific functions
"""

import platform
import re
import subprocess
from typing import Any, Tuple

import urwid
from typing_extensions import Literal


# PYTHON DETECTION
def detected_python() -> Tuple[str, str, str]:
    return (
        platform.python_version(),
        platform.python_implementation(),
        platform.python_branch(),
    )


def detected_python_in_full() -> str:
    version, implementation, branch = detected_python()
    branch_text = f"[{branch}]" if branch else ""
    return f"{version} ({implementation}) {branch_text}"


def detected_python_short() -> str:
    """Concise output for comparison in CI (CPython implied in version)"""
    version, implementation, _ = detected_python()
    short_version = version[: version.rfind(".")]
    if implementation == "CPython":
        return short_version
    if implementation == "PyPy":
        return f"pypy-{short_version}"
    raise NotImplementedError


# PLATFORM DETECTION
SupportedPlatforms = Literal["Linux", "MacOS", "WSL"]
AllPlatforms = Literal[SupportedPlatforms, "Unsupported"]

raw_platform = platform.system()

PLATFORM: AllPlatforms

if raw_platform == "Linux":
    PLATFORM = "WSL" if "microsoft" in platform.release().lower() else "Linux"
    # platform.release() seems to give kernel version - hence microsoft for WSL?
    # TODO: In future freedesktop_os_release() can give more detail (python 3.10)
    PLATFORM_DETAIL = f"kernel {platform.release()}"
elif raw_platform == "Darwin":
    PLATFORM = "MacOS"
    # platform.release() gives kernel version, but this gives OS & architecture
    mac_ver = platform.mac_ver()
    PLATFORM_DETAIL = f"{mac_ver[0]} on {mac_ver[2]}"
elif raw_platform == "Windows":
    PLATFORM = "Unsupported"
    # platform.win32_ver() gives more information as a tuple
    # Note that this includes Windows here, since it is not a supported native platform
    PLATFORM_DETAIL = f"Windows {platform.release()}"
else:
    PLATFORM = "Unsupported"
    PLATFORM_DETAIL = platform.release()


# PLATFORM DEPENDENT HELPERS
MOUSE_SELECTION_KEY = "Fn + Alt" if PLATFORM == "MacOS" else "Shift"


def detected_platform() -> str:
    print(f"{PLATFORM} ({PLATFORM_DETAIL})")
    return PLATFORM


class Screen(urwid.raw_display.Screen):
    def write(self, data: Any) -> None:
        if PLATFORM == "WSL":
            # replace urwid's SI/SO, which produce artifacts under WSL.
            # https://github.com/urwid/urwid/issues/264#issuecomment-358633735
            # Above link describes the change.
            data = re.sub("[\x0e\x0f]", "", data)
        super().write(data)


def generate_screen() -> Screen:
    return Screen()


def notify(title: str, text: str) -> str:
    command_list = None
    if PLATFORM == "MacOS":
        command_list = [
            "osascript",
            "-e",
            "on run(argv)",
            "-e",
            "return display notification item 1 of argv with title "
            'item 2 of argv sound name "ZT_NOTIFICATION_SOUND"',
            "-e",
            "end",
            "--",
            text,
            title,
        ]
    elif PLATFORM == "Linux":
        command_list = ["notify-send", "--", title, text]

    if command_list is not None:
        try:
            subprocess.run(
                command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            # This likely means the notification command could not be found
            return command_list[0]
    return ""


def successful_GUI_return_code() -> int:  # noqa: N802 (allow upper case)
    """
    Returns success return code for GUI commands, which are OS specific.
    """
    # WSL uses GUI return code as 1. Refer below link to know more:
    # https://stackoverflow.com/questions/52423031/
    # why-does-opening-an-explorer-window-and-selecting-a-file-through-pythons-subpro/
    # 52423798#52423798
    if PLATFORM == "WSL":
        return 1

    return 0


def normalized_file_path(path: str) -> str:
    """
    Returns file paths which are normalized as per platform.
    """
    # Convert Unix path to Windows path for WSL
    if PLATFORM == "WSL":
        return path.replace("/", "\\")

    return path
