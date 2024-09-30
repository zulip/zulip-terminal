"""
Detection of supported platforms & platform-specific functions
"""

import platform
import subprocess
from typing import Tuple

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
AllPlatforms = Literal[SupportedPlatforms, "unsupported"]

raw_platform = platform.system()

PLATFORM: AllPlatforms

if raw_platform == "Linux":
    PLATFORM = "WSL" if "microsoft" in platform.release().lower() else "Linux"
elif raw_platform == "Darwin":
    PLATFORM = "MacOS"
else:
    PLATFORM = "unsupported"


# PLATFORM DEPENDENT HELPERS
MOUSE_SELECTION_KEY = "Fn + Alt" if PLATFORM == "MacOS" else "Shift"


def detected_platform() -> str:
    return PLATFORM


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


def process_media_tool() -> str:
    """
    Returns the media tool command as per platform.
    """
    if PLATFORM == "WSL":
        tool = "explorer.exe"
    elif PLATFORM == "Linux":
        tool = "xdg-open"
    elif PLATFORM == "MacOS":
        tool = "open"
    else:
        tool = "invalid"

    return tool
