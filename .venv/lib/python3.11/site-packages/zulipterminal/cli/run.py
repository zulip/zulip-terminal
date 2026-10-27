"""
Marks the entry point into the application
"""

import argparse
import configparser
import logging
import os
import stat
import sys
import traceback
from enum import Enum
from os import path, remove
from typing import Dict, List, NamedTuple, Optional, Tuple

import requests
from urwid import display_common, set_encoding

from zulipterminal.api_types import ServerSettings
from zulipterminal.config.themes import (
    ThemeError,
    aliased_themes,
    all_themes,
    complete_and_incomplete_themes,
    generate_theme,
)
from zulipterminal.core import Controller
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.platform_code import detected_platform, detected_python_in_full
from zulipterminal.version import ZT_VERSION


class ConfigSource(Enum):
    DEFAULT = "from default config"
    ZULIPRC = "in zuliprc file"
    ENV = "from environment"
    COMMANDLINE = "on command line"


class SettingData(NamedTuple):
    value: str
    source: ConfigSource


TRACEBACK_LOG_FILENAME = "zulip-terminal-tracebacks.log"
API_CALL_LOG_FILENAME = "zulip-terminal-API-requests.log"

# Create a logger for this application
zt_logger = logging.getLogger(__name__)
zt_logger.setLevel(logging.DEBUG)
zt_logfile_handler = logging.FileHandler(
    TRACEBACK_LOG_FILENAME,
    delay=True,  # Don't open the file until there's a logging event
)
zt_logger.addHandler(zt_logfile_handler)

# Route requests details (API calls) to separate file
requests_logger = logging.getLogger("urllib3")
requests_logger.setLevel(logging.DEBUG)

# Valid boolean settings, which map from (str, str) to (True, False)
VALID_BOOLEAN_SETTINGS: Dict[str, Tuple[str, str]] = {
    "autohide": ("autohide", "no_autohide"),
    "notify": ("enabled", "disabled"),
    "exit_confirmation": ("enabled", "disabled"),
    "transparency": ("enabled", "disabled"),
}

COLOR_DEPTH_ARGS_TO_DEPTHS: Dict[str, int] = {
    "1": 1,
    "16": 16,
    "256": 256,
    "24bit": 2**24,
}

# These should be the defaults without config file or command-line overrides
DEFAULT_SETTINGS = {
    "theme": "zt_dark",
    "autohide": "no_autohide",
    "notify": "disabled",
    "footlinks": "enabled",
    "color-depth": "256",
    "maximum-footlinks": "3",
    "exit_confirmation": "enabled",
    "transparency": "disabled",
    "editor": "",
}
assert DEFAULT_SETTINGS["autohide"] in VALID_BOOLEAN_SETTINGS["autohide"]
assert DEFAULT_SETTINGS["notify"] in VALID_BOOLEAN_SETTINGS["notify"]
assert DEFAULT_SETTINGS["color-depth"] in COLOR_DEPTH_ARGS_TO_DEPTHS
assert (
    DEFAULT_SETTINGS["exit_confirmation"] in VALID_BOOLEAN_SETTINGS["exit_confirmation"]
)
assert DEFAULT_SETTINGS["transparency"] in VALID_BOOLEAN_SETTINGS["transparency"]


def in_color(color: str, text: str) -> str:
    color_for_str = {
        "red": "1",
        "green": "2",
        "yellow": "3",
        "blue": "4",
        "purple": "5",
        "cyan": "6",
    }
    # We can use 3 instead of 9 if high-contrast is eg. less compatible?
    return f"\033[9{color_for_str[color]}m{text}\033[0m"


def exit_with_error(
    error_message: str, *, helper_text: str = "", error_code: int = 1
) -> None:
    print(in_color("red", error_message))
    if helper_text:
        print(helper_text)
    sys.exit(error_code)


def parse_args(argv: List[str]) -> argparse.Namespace:
    description = """
        Starts Zulip-Terminal.
        """
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description=description, formatter_class=formatter_class
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="show zulip-terminal version and exit",
    )
    parser.add_argument(
        "--config-file",
        "-c",
        action="store",
        help="config file downloaded from your zulip "
        "organization (default: ~/zuliprc)",
    )
    parser.add_argument(
        "--theme",
        "-t",
        help=f"choose color theme (default: {DEFAULT_SETTINGS['theme']})",
    )
    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="list all the color themes and exit",
    )
    parser.add_argument(
        "--color-depth",
        choices=COLOR_DEPTH_ARGS_TO_DEPTHS,
        help=f"force the color depth (default: {DEFAULT_SETTINGS['color-depth']})",
    )
    parser.add_argument(
        "-e",
        "--explore",
        action="store_true",
        help="do not mark messages as read in the session",
    )

    transparency_group = parser.add_mutually_exclusive_group()
    transparency_group.add_argument(
        "--transparency",
        dest="transparency",
        action="store_const",
        const="enabled",
        help="enable transparent background (if supported by theme and terminal)",
    )
    transparency_group.add_argument(
        "--no-transparency",
        dest="transparency",
        action="store_const",
        const="disabled",
        help="disable transparent background",
    )

    notify_group = parser.add_mutually_exclusive_group()
    notify_group.add_argument(
        "--notify",
        dest="notify",
        default=None,
        action="store_const",
        const="enabled",
        help="enable desktop notifications",
    )
    notify_group.add_argument(
        "--no-notify",
        dest="notify",
        default=None,
        action="store_const",
        const="disabled",
        help="disable desktop notifications",
    )

    autohide_group = parser.add_mutually_exclusive_group()
    autohide_group.add_argument(
        "--autohide",
        dest="autohide",
        default=None,
        action="store_const",
        const="autohide",
        help="autohide list of users and streams",
    )
    autohide_group.add_argument(
        "--no-autohide",
        dest="autohide",
        default=None,
        action="store_const",
        const="no_autohide",
        help="don't autohide list of users and streams",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug mode",
    )
    parser.add_argument(
        "--profile",
        dest="profile",
        action="store_true",
        default=False,
        help="profile runtime",
    )

    return parser.parse_args(argv)


def styled_input(label: str) -> str:
    return input(in_color("blue", label))


def get_login_label(server_properties: ServerSettings) -> str:
    require_email_format_usernames = server_properties["require_email_format_usernames"]
    email_auth_enabled = server_properties["email_auth_enabled"]

    if not require_email_format_usernames and email_auth_enabled:
        return "Email or Username: "
    elif not require_email_format_usernames:
        return "Username: "
    else:
        # TODO: Validate Email address
        return "Email: "


class NotAZulipOrganizationError(Exception):
    pass


def get_server_settings(realm_url: str) -> ServerSettings:
    response = requests.get(url=f"{realm_url}/api/v1/server_settings")
    if response.status_code != requests.codes.OK:
        raise NotAZulipOrganizationError(realm_url)
    return response.json()


def get_api_key(realm_url: str) -> Optional[Tuple[str, str, str]]:
    from getpass import getpass

    try:
        server_properties = get_server_settings(realm_url)
    except NotAZulipOrganizationError:
        exit_with_error(f"No Zulip Organization found at {realm_url}.")

    # Assuming we connect to and get data from the server, use the realm_url it suggests
    # This avoids cases where there are redirects between http and https, for example
    preferred_realm_url = server_properties["realm_uri"]

    login_id_label = get_login_label(server_properties)
    login_id = styled_input(login_id_label)
    password = getpass(in_color("blue", "Password: "))

    response = requests.post(
        url=f"{preferred_realm_url}/api/v1/fetch_api_key",
        data={
            "username": login_id,
            "password": password,
        },
    )
    if response.status_code == requests.codes.OK:
        return preferred_realm_url, login_id, str(response.json()["api_key"])
    return None


def fetch_zuliprc(zuliprc_path: str) -> None:
    print(
        f"{in_color('red', f'zuliprc file was not found at {zuliprc_path}')}"
        f"\nPlease enter your credentials to login into your Zulip organization."
        f"\n"
        f"\nNOTE: The {in_color('blue', 'Zulip server URL')}"
        f" is where you would go in a web browser to log in to Zulip."
        f"\nIt often looks like one of the following:"
        f"\n   {in_color('green', 'your-org.zulipchat.com')} (Zulip cloud)"
        f"\n   {in_color('green', 'zulip.your-org.com')} (self-hosted servers)"
        f"\n   {in_color('green', 'chat.zulip.org')} (the Zulip community server)"
    )
    realm_url = styled_input("Zulip server URL: ")
    if realm_url.startswith("localhost"):
        realm_url = f"http://{realm_url}"
    elif not realm_url.startswith("http"):
        realm_url = f"https://{realm_url}"
    # Remove trailing "/"s from realm_url to simplify the below logic
    # for adding "/api"
    realm_url = realm_url.rstrip("/")
    login_data = get_api_key(realm_url)

    while login_data is None:
        print(in_color("red", "\nIncorrect Email(or Username) or Password!\n"))
        login_data = get_api_key(realm_url)

    preferred_realm_url, login_id, api_key = login_data
    save_zuliprc_failure = _write_zuliprc(
        zuliprc_path,
        login_id=login_id,
        api_key=api_key,
        server_url=preferred_realm_url,
    )
    if not save_zuliprc_failure:
        print(f"Generated API key saved at {zuliprc_path}")
    else:
        exit_with_error(save_zuliprc_failure)


def _write_zuliprc(
    to_path: str, *, login_id: str, api_key: str, server_url: str
) -> str:
    """
    Writes a zuliprc file, returning a non-empty error string on failure
    Only creates new private files; errors if file already exists
    """
    try:
        with open(
            os.open(to_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600), "w"
        ) as f:
            f.write(f"[api]\nemail={login_id}\nkey={api_key}\nsite={server_url}")
        return ""
    except FileExistsError:
        return f"zuliprc already exists at {to_path}"
    except OSError as ex:
        return f"{ex.__class__.__name__}: zuliprc could not be created at {to_path}"


def parse_zuliprc(zuliprc_str: str) -> Dict[str, SettingData]:
    zuliprc_path = path.expanduser(zuliprc_str)
    while not path.exists(zuliprc_path):
        try:
            fetch_zuliprc(zuliprc_path)
        # Invalid user inputs (e.g. pressing arrow keys) may cause ValueError
        except (OSError, ValueError):
            # Remove zuliprc file if created.
            if path.exists(zuliprc_path):
                remove(zuliprc_path)
            print(in_color("red", "\nInvalid Credentials, Please try again!\n"))
        except EOFError:
            # Assume that the user pressed Ctrl+D and continue the loop
            print("\n")

    mode = os.stat(zuliprc_path).st_mode
    is_readable_by_group_or_others = mode & (stat.S_IRWXG | stat.S_IRWXO)

    if is_readable_by_group_or_others:
        print(
            in_color(
                "red",
                "ERROR: Please ensure your zuliprc is NOT publicly accessible:\n"
                f"  {zuliprc_path}\n"
                f"(it currently has permissions '{stat.filemode(mode)}')\n"
                "This can often be achieved with a command such as:\n"
                f"  chmod og-rwx {zuliprc_path}\n"
                "Consider regenerating the [api] part of your zuliprc to ensure "
                "your account is secure.",
            )
        )
        sys.exit(1)

    zuliprc = configparser.ConfigParser()

    try:
        res = zuliprc.read(zuliprc_path)
        if len(res) == 0:
            exit_with_error(f"Could not access zuliprc file at {zuliprc_path}")
    except configparser.MissingSectionHeaderError:
        exit_with_error(f"Failed to parse zuliprc file at {zuliprc_path}")

    # Initialize with default settings
    settings = {
        setting: SettingData(default, ConfigSource.DEFAULT)
        for setting, default in DEFAULT_SETTINGS.items()
    }

    if "zterm" in zuliprc:
        config = zuliprc["zterm"]
        for conf in config:
            settings[conf] = SettingData(config[conf], ConfigSource.ZULIPRC)

    return settings


def list_themes() -> str:
    available_themes = all_themes()
    text = "The following themes are available:\n"
    for theme in available_themes:
        suffix = ""
        if theme == DEFAULT_SETTINGS["theme"]:
            suffix += "[default theme]"
        text += f"  {theme} {suffix}\n"
    return text + (
        "Specify theme in zuliprc file or override "
        "using -t/--theme options on command line."
    )


def main(options: Optional[List[str]] = None) -> None:
    """
    Launch Zulip Terminal.
    """

    argv = options if options is not None else sys.argv[1:]
    args = parse_args(argv)

    set_encoding("utf-8")

    if args.debug:
        debug_path: Optional[str] = "debug.log"
        assert isinstance(debug_path, str)
        print(
            "NOTE: Debug mode enabled:"
            f"\n  API calls will be logged to {in_color('blue', API_CALL_LOG_FILENAME)}"
            f"\n  Standard output being logged to {in_color('blue', debug_path)}"
        )
        requests_logfile_handler = logging.FileHandler(API_CALL_LOG_FILENAME)
        requests_logger.addHandler(requests_logfile_handler)
    else:
        debug_path = None
        requests_logger.addHandler(logging.NullHandler())

    if args.profile:
        import cProfile

        prof = cProfile.Profile()
        prof.enable()

    if args.version:
        print(f"Zulip Terminal {ZT_VERSION}")
        sys.exit(0)

    if args.list_themes:
        print(list_themes())
        sys.exit(0)

    if args.config_file:
        zuliprc_path = args.config_file
    else:
        zuliprc_path = "~/zuliprc"

    print(
        "Detected:"
        f"\n - platform: {detected_platform()}"
        f"\n - python: {detected_python_in_full()}"
    )

    try:
        zterm = parse_zuliprc(zuliprc_path)

        ### Validate footlinks settings (not from command line)
        if (
            zterm["footlinks"].source == ConfigSource.ZULIPRC
            and zterm["maximum-footlinks"].source == ConfigSource.ZULIPRC
        ):
            exit_with_error(
                "Configuration Error: "
                "footlinks and maximum-footlinks options cannot be used together"
            )

        if zterm["maximum-footlinks"].source == ConfigSource.ZULIPRC:
            maximum_footlinks = int(zterm["maximum-footlinks"].value)
            if maximum_footlinks < 0:
                exit_with_error(
                    "Configuration Error: "
                    "Minimum value allowed for maximum-footlinks is 0; "
                    f"you used '{maximum_footlinks}'"
                )

        if zterm["footlinks"].source == ConfigSource.ZULIPRC:
            if zterm["footlinks"].value == DEFAULT_SETTINGS["footlinks"]:
                maximum_footlinks = 3
            else:
                maximum_footlinks = 0
        else:
            maximum_footlinks = int(zterm["maximum-footlinks"].value)

        ### Load theme override & validate
        if args.theme:
            theme_to_use = SettingData(args.theme, ConfigSource.COMMANDLINE)
        else:
            theme_to_use = zterm["theme"]

        theme_alias_suffix = ""
        available_themes = all_themes()
        theme_aliases = aliased_themes()
        is_valid_theme = (
            theme_to_use.value in available_themes
            or theme_to_use.value in theme_aliases
        )
        if not is_valid_theme:
            exit_with_error(
                "Invalid theme '{}' was specified {}.".format(*theme_to_use),
                helper_text=list_themes(),
            )
        if theme_to_use.value not in available_themes:
            # theme must be an alias, as it is valid
            theme_alias_suffix = f" (by alias '{theme_to_use.value}')"
            real_theme_name = theme_aliases[theme_to_use.value]
            theme_to_use = SettingData(real_theme_name, theme_to_use.source)

        ### Load overrides & validate remaining settings
        if args.transparency:
            zterm["transparency"] = SettingData(
                args.transparency, ConfigSource.COMMANDLINE
            )

        if args.autohide:
            zterm["autohide"] = SettingData(args.autohide, ConfigSource.COMMANDLINE)

        if args.color_depth:
            zterm["color-depth"] = SettingData(
                args.color_depth, ConfigSource.COMMANDLINE
            )

        if args.notify:
            zterm["notify"] = SettingData(args.notify, ConfigSource.COMMANDLINE)

        valid_remaining_settings = dict(
            VALID_BOOLEAN_SETTINGS,
            **{"color-depth": COLOR_DEPTH_ARGS_TO_DEPTHS},
        )

        # Validate remaining settings
        for setting, valid_remaining_values in valid_remaining_settings.items():
            if zterm[setting].value not in valid_remaining_values:
                helper_text = (
                    ["Valid values are:"]
                    + [f"  {option}" for option in valid_remaining_values]
                    + [f"Specify the {setting} option in zuliprc file."]
                )
                exit_with_error(
                    "Invalid {} setting '{}' was specified {}.".format(
                        setting, *zterm[setting]
                    ),
                    helper_text="\n".join(helper_text),
                )

        def print_setting(setting: str, data: SettingData, suffix: str = "") -> None:
            print(f"   {setting} '{data.value}' specified {data.source.value}{suffix}.")

        ### Let the user know we're starting to load, with what options, from where
        print("Loading with:")
        print_setting("theme", theme_to_use, theme_alias_suffix)
        complete, incomplete = complete_and_incomplete_themes()
        if theme_to_use.value in incomplete:
            incomplete_theme_text = "   WARNING: Incomplete theme; results may vary!\n"
            if complete:
                incomplete_theme_text += f"      (you could try: {', '.join(complete)})"
            else:
                incomplete_theme_text += "      (all themes are incomplete)"
            print(in_color("yellow", incomplete_theme_text))
        print_setting("autohide setting", zterm["autohide"])
        print_setting("exit confirmation setting", zterm["exit_confirmation"])
        if zterm["footlinks"].source == ConfigSource.ZULIPRC:
            print_setting(
                "maximum footlinks value",
                SettingData(str(maximum_footlinks), zterm["footlinks"].source),
                " from footlinks",
            )
        else:
            print_setting("maximum footlinks value", zterm["maximum-footlinks"])
        print_setting("color depth setting", zterm["color-depth"])
        print_setting("notify setting", zterm["notify"])
        print_setting("transparency setting", zterm["transparency"])

        if zterm["editor"].source == ConfigSource.ZULIPRC:
            editor_command = zterm["editor"].value
            editor_config_source = ConfigSource.ZULIPRC
        else:
            editor_command = os.environ.get(
                "ZULIP_EDITOR_COMMAND",
                os.environ.get("EDITOR", ""),
            )
            editor_config_source = ConfigSource.ENV

        print_setting(
            "external editor command",
            SettingData(editor_command, editor_config_source),
        )

        ### Generate data not output to user, but into Controller
        # Translate valid strings for boolean values into True/False
        boolean_settings: Dict[str, bool] = dict()
        for setting, valid_values in VALID_BOOLEAN_SETTINGS.items():
            boolean_settings[setting] = zterm[setting].value == valid_values[0]

        # Generate urwid palette
        color_depth_str = zterm["color-depth"].value
        color_depth = COLOR_DEPTH_ARGS_TO_DEPTHS[color_depth_str]
        transparency_enabled = boolean_settings["transparency"]

        theme_data = generate_theme(
            theme_to_use.value,
            color_depth=color_depth,
            transparent_background=transparency_enabled,
        )

        Controller(
            config_file=zuliprc_path,
            maximum_footlinks=maximum_footlinks,
            theme_name=theme_to_use.value,
            theme=theme_data,
            color_depth=color_depth,
            in_explore_mode=args.explore,
            **boolean_settings,
            debug_path=debug_path,
            editor_command=editor_command,
        ).main()
    except ServerConnectionFailure as e:
        # Acts as separator between logs
        zt_logger.info("\n\n%s\n\n", e)
        zt_logger.exception(e)
        exit_with_error(f"\nError connecting to Zulip server: {e}.")
    except ThemeError as e:
        # Acts as separator between logs
        zt_logger.info("\n\n%s\n\n", e)
        zt_logger.exception(e)
        exit_with_error(f"\n{e}")
    except (display_common.AttrSpecError, display_common.ScreenError) as e:
        # NOTE: Strictly this is not necessarily just a theme error
        # FIXME: Add test for this - once loading takes place after UI setup

        # Acts as separator between logs
        zt_logger.info("\n\n%s\n\n", e)
        zt_logger.exception(e)
        exit_with_error(f"\nPossible theme error: {e}.")
    except Exception as e:
        zt_logger.info("\n\n{e}\n\n")
        zt_logger.exception(e)
        if args.debug:
            sys.stdout.flush()
            traceback.print_exc(file=sys.stderr)
            run_debugger = input("Run Debugger? (y/n): ")
            if run_debugger in ["y", "Y", "yes"]:
                # Open PUDB Debugger
                import pudb

                pudb.post_mortem()

        if hasattr(e, "extra_info"):
            print(in_color("red", f"\n{e.extra_info}"), file=sys.stderr)

        print(
            in_color(
                "red",
                "\nZulip Terminal has crashed!"
                f"\nPlease refer to {TRACEBACK_LOG_FILENAME}"
                " for full log of the error.",
            ),
            file=sys.stderr,
        )
        print(
            "You can ask for help at:"
            "\nhttps://chat.zulip.org/#narrow/stream/206-zulip-terminal",
            file=sys.stderr,
        )
        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.stderr.flush()

    finally:
        if args.profile:
            prof.disable()
            import tempfile

            with tempfile.NamedTemporaryFile(
                prefix="zulip_term_profile.", suffix=".dat", delete=False
            ) as profile_file:
                profile_path = profile_file.name
            # Dump stats only after temporary file is closed (for Win NT+ case)
            prof.dump_stats(profile_path)
            print(
                f"Profile data saved to {profile_path}.\n"
                f"You can visualize it using e.g. `snakeviz {profile_path}`"
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
