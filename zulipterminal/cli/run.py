import argparse
import configparser
import logging
import os
import stat
import sys
import traceback
from os import path, remove
from typing import Any, Dict, List, Optional, Tuple

import requests
from urwid import display_common, set_encoding

from zulipterminal.config.themes import (
    InvalidThemeColorCode,
    aliased_themes,
    all_themes,
    complete_and_incomplete_themes,
    generate_theme,
)
from zulipterminal.core import Controller
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.version import ZT_VERSION


TRACEBACK_LOG_FILENAME = "zulip-terminal-tracebacks.log"
API_CALL_LOG_FILENAME = "zulip-terminal-API-requests.log"
ZULIPRC_CONFIG = "in zuliprc file"
NO_CONFIG = "with no config"

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

# These should be the defaults without config file or command-line overrides
DEFAULT_SETTINGS = {
    "theme": "zt_dark",
    "autohide": "no_autohide",
    "notify": "disabled",
    "footlinks": "enabled",
    "color-depth": "256",
    "maximum-footlinks": "3",
}


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
        choices=["1", "16", "256", "24bit"],
        help=f"force the color depth (default: {DEFAULT_SETTINGS['color-depth']})",
    )
    parser.add_argument(
        "-e",
        "--explore",
        action="store_true",
        help="do not mark messages as read in the session",
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


def get_login_id(realm_url: str) -> str:
    res_json = requests.get(url=f"{realm_url}/api/v1/server_settings").json()
    require_email_format_usernames = res_json["require_email_format_usernames"]
    email_auth_enabled = res_json["email_auth_enabled"]

    if not require_email_format_usernames and email_auth_enabled:
        label = "Email or Username: "
    elif not require_email_format_usernames:
        label = "Username: "
    else:
        # TODO: Validate Email address
        label = "Email: "

    return styled_input(label)


def get_api_key(realm_url: str) -> Tuple[requests.Response, str]:
    from getpass import getpass

    login_id = get_login_id(realm_url)
    password = getpass(in_color("blue", "Password: "))
    response = requests.post(
        url=f"{realm_url}/api/v1/fetch_api_key",
        data={
            "username": login_id,
            "password": password,
        },
    )
    return response, login_id


def fetch_zuliprc(zuliprc_path: str) -> None:
    print(
        f"{in_color('red', f'zuliprc file was not found at {zuliprc_path}')}"
        f"\nPlease enter your credentials to login into your Zulip organization."
        f"\n"
        f"\nNOTE: The {in_color('blue', 'Zulip URL')}"
        f" is where you would go in a web browser to log in to Zulip."
        f"\nIt often looks like one of the following:"
        f"\n   {in_color('green', 'your-org.zulipchat.com')} (Zulip cloud)"
        f"\n   {in_color('green', 'zulip.your-org.com')} (self-hosted servers)"
        f"\n   {in_color('green', 'chat.zulip.org')} (the Zulip community server)"
    )
    realm_url = styled_input("Zulip URL: ")
    if realm_url.startswith("localhost"):
        realm_url = f"http://{realm_url}"
    elif not realm_url.startswith("http"):
        realm_url = f"https://{realm_url}"
    # Remove trailing "/"s from realm_url to simplify the below logic
    # for adding "/api"
    realm_url = realm_url.rstrip("/")
    res, login_id = get_api_key(realm_url)

    while res.status_code != 200:
        print(in_color("red", "\nIncorrect Email(or Username) or Password!\n"))
        res, login_id = get_api_key(realm_url)

    save_zuliprc_failure = _write_zuliprc(
        zuliprc_path,
        login_id=login_id,
        api_key=str(res.json()["api_key"]),
        server_url=realm_url,
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
    except FileExistsError as ex:
        return f"zuliprc already exists at {to_path}"
    except OSError as ex:
        return f"{ex.__class__.__name__}: zuliprc could not be created at {to_path}"


def parse_zuliprc(zuliprc_str: str) -> Dict[str, Any]:
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
                "  {0}\n"
                "(it currently has permissions '{1}')\n"
                "This can often be achieved with a command such as:\n"
                "  chmod og-rwx {0}\n"
                "Consider regenerating the [api] part of your zuliprc to ensure "
                "your account is secure.".format(zuliprc_path, stat.filemode(mode)),
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
    NO_CONFIG = "with no config"
    settings = {
        setting: (default, NO_CONFIG) for setting, default in DEFAULT_SETTINGS.items()
    }

    if "zterm" in zuliprc:
        config = zuliprc["zterm"]
        for conf in config:
            settings[conf] = (config[conf], ZULIPRC_CONFIG)

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

    try:
        zterm = parse_zuliprc(zuliprc_path)

        if args.autohide:
            zterm["autohide"] = (args.autohide, "on command line")

        if args.theme:
            theme_to_use = (args.theme, "on command line")
        else:
            theme_to_use = zterm["theme"]

        if (
            zterm["footlinks"][1] == ZULIPRC_CONFIG
            and zterm["maximum-footlinks"][1] == ZULIPRC_CONFIG
        ):
            exit_with_error(
                "Footlinks property is not allowed alongside maximum-footlinks"
            )

        if (
            zterm["maximum-footlinks"][1] == ZULIPRC_CONFIG
            and int(zterm["maximum-footlinks"][0]) < 0
        ):
            exit_with_error("Minimum value allowed for maximum-footlinks is 0")

        if zterm["footlinks"][1] == ZULIPRC_CONFIG:
            if zterm["footlinks"][0] == DEFAULT_SETTINGS["footlinks"]:
                maximum_footlinks = 3
            else:
                maximum_footlinks = 0
        else:
            maximum_footlinks = int(zterm["maximum-footlinks"][0])

        available_themes = all_themes()
        theme_aliases = aliased_themes()
        is_valid_theme = (
            theme_to_use[0] in available_themes or theme_to_use[0] in theme_aliases
        )
        if not is_valid_theme:
            exit_with_error(
                "Invalid theme '{}' was specified {}.".format(*theme_to_use),
                helper_text=list_themes(),
            )
        if theme_to_use[0] not in available_themes:
            # theme must be an alias, as it is valid
            real_theme_name = theme_aliases[theme_to_use[0]]
            theme_to_use = (
                real_theme_name,
                "{} (by alias '{}')".format(theme_to_use[1], theme_to_use[0]),
            )

        if args.color_depth:
            zterm["color-depth"] = (args.color_depth, "on command line")

        color_depth_str = zterm["color-depth"][0]
        if color_depth_str == "24bit":
            color_depth = 2**24
        else:
            color_depth = int(color_depth_str)

        if args.notify:
            zterm["notify"] = (args.notify, "on command line")

        print("Loading with:")
        print("   theme '{}' specified {}.".format(*theme_to_use))
        complete, incomplete = complete_and_incomplete_themes()
        if theme_to_use[0] in incomplete:
            if complete:
                incomplete_theme_warning = (
                    "   WARNING: Incomplete theme; results may vary!\n"
                    "      (you could try: {})".format(", ".join(complete))
                )
            else:
                incomplete_theme_warning = (
                    "   WARNING: Incomplete theme; results may vary!\n"
                    "      (all themes are incomplete)"
                )
            print(in_color("yellow", incomplete_theme_warning))
        print("   autohide setting '{}' specified {}.".format(*zterm["autohide"]))
        if zterm["footlinks"][1] == ZULIPRC_CONFIG:
            print(
                "   maximum footlinks value '{}' specified {} from footlinks.".format(
                    maximum_footlinks, zterm["footlinks"][1]
                )
            )
        else:
            print(
                "   maximum footlinks value '{}' specified {}.".format(
                    *zterm["maximum-footlinks"]
                )
            )
        print("   color depth setting '{}' specified {}.".format(*zterm["color-depth"]))
        print("   notify setting '{}' specified {}.".format(*zterm["notify"]))

        # For binary settings
        # Specify setting in order True, False
        valid_settings = {
            "autohide": ["autohide", "no_autohide"],
            "notify": ["enabled", "disabled"],
            "color-depth": ["1", "16", "256", "24bit"],
        }
        boolean_settings: Dict[str, bool] = dict()
        for setting, valid_values in valid_settings.items():
            if zterm[setting][0] not in valid_values:
                helper_text = (
                    ["Valid values are:"]
                    + [f"  {option}" for option in valid_values]
                    + [f"Specify the {setting} option in zuliprc file."]
                )
                exit_with_error(
                    "Invalid {} setting '{}' was specified {}.".format(
                        setting, *zterm[setting]
                    ),
                    helper_text="\n".join(helper_text),
                )
            if setting == "color-depth":
                break
            boolean_settings[setting] = zterm[setting][0] == valid_values[0]

        theme_data = generate_theme(theme_to_use[0], color_depth)

        Controller(
            config_file=zuliprc_path,
            maximum_footlinks=maximum_footlinks,
            theme_name=theme_to_use[0],
            theme=theme_data,
            color_depth=color_depth,
            in_explore_mode=args.explore,
            **boolean_settings,
            debug_path=debug_path,
        ).main()
    except ServerConnectionFailure as e:
        # Acts as separator between logs
        zt_logger.info(f"\n\n{e}\n\n")
        zt_logger.exception(e)
        exit_with_error(f"\nError connecting to Zulip server: {e}.")
    except InvalidThemeColorCode as e:
        # Acts as separator between logs
        zt_logger.info(f"\n\n{e}\n\n")
        zt_logger.exception(e)
        exit_with_error(f"\n{e}")
    except (display_common.AttrSpecError, display_common.ScreenError) as e:
        # NOTE: Strictly this is not necessarily just a theme error
        # FIXME: Add test for this - once loading takes place after UI setup

        # Acts as separator between logs
        zt_logger.info(f"\n\n{e}\n\n")
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
            print(in_color("red", f"\n{e.extra_info}"), file=sys.stderr)  # type: ignore

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
                "Profile data saved to {0}.\n"
                "You can visualize it using e.g. `snakeviz {0}`".format(profile_path)
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
