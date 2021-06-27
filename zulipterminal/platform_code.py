import platform

from typing_extensions import Literal


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
