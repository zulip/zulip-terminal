import argparse
import json
import logging
import optparse
import os
import platform
import random
import sys
import time
import traceback
import types
import urllib.parse
from configparser import ConfigParser
from typing import (
    IO,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import distro
import requests
from typing_extensions import Literal

__version__ = "0.8.2"

# Ensure the Python version is supported
assert sys.version_info >= (3, 6)

logger = logging.getLogger(__name__)

# In newer versions, the 'json' attribute is a function, not a property
requests_json_is_function = callable(requests.Response.json)

API_VERSTRING = "v1/"

# An optional parameter to `move_topic` and `update_message` actions
# See eg. https://zulip.com/api/update-message#parameter-propagate_mode
EditPropagateMode = Literal["change_one", "change_all", "change_later"]

# Generally a `reaction_type` is present whenever an emoji is specified:
# - Optional parameters to actions: `add_reaction`, `remove_reaction`
# - Events: "user_status", "reaction", "message", "update_message"
# - Inside each reaction in the `reactions` field of returned message objects.
EmojiType = Literal["realm_emoji", "unicode_emoji", "zulip_extra_emoji"]

# Message flags which may be directly modified by the current user:
# - Updated by `update_message_flags` (and for the `read` flag, also
#   the `mark_all_as_read`, `mark_stream_as_read`, and
#   `mark_topic_as_read` actions).
# - User is notified of changes via `update_message_flags` events.
# See subset of https://zulip.com/api/update-message-flags#available-flags
ModifiableMessageFlag = Literal["read", "starred", "collapsed"]

# All possible message flags.
# - Generally present in `flags` object of returned message objects.
# - User is notified of changes via "update_message_flags" and `update_message`
#   events. The latter is important for clients to learn when a message is
#   edited to mention the current user or contain an alert word.
# See https://zulip.com/api/update-message-flags#available-flags
MessageFlag = Literal[
    ModifiableMessageFlag,
    "mentioned",
    "wildcard_mentioned",
    "has_alert_word",
    "historical",
]


class CountingBackoff:
    def __init__(
        self,
        maximum_retries: int = 10,
        timeout_success_equivalent: Optional[float] = None,
        delay_cap: float = 90.0,
    ) -> None:
        """Sets up a retry-backoff object.  Example usage:
        backoff = zulip.CountingBackoff()
        while backoff.keep_going():
            try:
                something()
                backoff.succeed()
            except Exception:
                backoff.fail()

        timeout_success_equivalent is used in cases where 'success' is
        never possible to determine automatically; it sets the
        threshold in seconds before the next keep_going/fail, above
        which the last run is treated like it was a success.

        """
        self.number_of_retries = 0
        self.maximum_retries = maximum_retries
        self.timeout_success_equivalent = timeout_success_equivalent
        self.last_attempt_time = 0.0
        self.delay_cap = delay_cap

    def keep_going(self) -> bool:
        self._check_success_timeout()
        return self.number_of_retries < self.maximum_retries

    def succeed(self) -> None:
        self.number_of_retries = 0
        self.last_attempt_time = time.time()

    def fail(self) -> None:
        self._check_success_timeout()
        self.number_of_retries = min(self.number_of_retries + 1, self.maximum_retries)
        self.last_attempt_time = time.time()

    def _check_success_timeout(self) -> None:
        if (
            self.timeout_success_equivalent is not None
            and self.last_attempt_time != 0
            and time.time() - self.last_attempt_time > self.timeout_success_equivalent
        ):
            self.number_of_retries = 0


class RandomExponentialBackoff(CountingBackoff):
    def fail(self) -> None:
        super().fail()
        # Exponential growth with ratio sqrt(2); compute random delay
        # between x and 2x where x is growing exponentially
        delay_scale = int(2 ** (self.number_of_retries / 2.0 - 1)) + 1
        delay = min(delay_scale + random.randint(1, delay_scale), self.delay_cap)
        message = f"Sleeping for {delay}s [max {delay_scale * 2}] before retrying."
        try:
            logger.warning(message)
        except NameError:
            print(message)
        time.sleep(delay)


def _default_client() -> str:
    return "ZulipPython/" + __version__


def add_default_arguments(
    parser: argparse.ArgumentParser,
    patch_error_handling: bool = True,
    allow_provisioning: bool = False,
) -> argparse.ArgumentParser:

    if patch_error_handling:

        def custom_error_handling(self: argparse.ArgumentParser, message: str) -> None:
            self.print_help(sys.stderr)
            self.exit(2, f"{self.prog}: error: {message}\n")

        parser.error = types.MethodType(custom_error_handling, parser)  # type: ignore # patching function

    if allow_provisioning:
        parser.add_argument(
            "--provision",
            action="store_true",
            dest="provision",
            help="install dependencies for this script (found in requirements.txt)",
        )

    group = parser.add_argument_group("Zulip API configuration")
    group.add_argument("--site", dest="zulip_site", help="Zulip server URI", default=None)
    group.add_argument("--api-key", dest="zulip_api_key", action="store")
    group.add_argument(
        "--user", dest="zulip_email", help="Email address of the calling bot or user."
    )
    group.add_argument(
        "--config-file",
        action="store",
        dest="zulip_config_file",
        help="""Location of an ini file containing the above
                            information. (default ~/.zuliprc)""",
    )
    group.add_argument("-v", "--verbose", action="store_true", help="Provide detailed output.")
    group.add_argument(
        "--client", action="store", default=None, dest="zulip_client", help=argparse.SUPPRESS
    )
    group.add_argument(
        "--insecure",
        action="store_true",
        dest="insecure",
        help="""Do not verify the server certificate.
                            The https connection will not be secure.""",
    )
    group.add_argument(
        "--cert-bundle",
        action="store",
        dest="cert_bundle",
        help="""Specify a file containing either the
                            server certificate, or a set of trusted
                            CA certificates. This will be used to
                            verify the server's identity. All
                            certificates should be PEM encoded.""",
    )
    group.add_argument(
        "--client-cert",
        action="store",
        dest="client_cert",
        help="""Specify a file containing a client
                            certificate (not needed for most deployments).""",
    )
    group.add_argument(
        "--client-cert-key",
        action="store",
        dest="client_cert_key",
        help="""Specify a file containing the client
                            certificate's key (if it is in a separate
                            file).""",
    )
    return parser


# This method might seem redundant with `add_default_arguments()`,
# except for the fact that is uses the deprecated `optparse` module.
# We still keep it for legacy support of out-of-tree bots and integrations
# depending on it.
def generate_option_group(parser: optparse.OptionParser, prefix: str = "") -> optparse.OptionGroup:
    logging.warning(
        """zulip.generate_option_group is based on optparse, which
                    is now deprecated. We recommend migrating to argparse and
                    using zulip.add_default_arguments instead."""
    )

    group = optparse.OptionGroup(parser, "Zulip API configuration")
    group.add_option(f"--{prefix}site", dest="zulip_site", help="Zulip server URI", default=None)
    group.add_option(f"--{prefix}api-key", dest="zulip_api_key", action="store")
    group.add_option(
        f"--{prefix}user",
        dest="zulip_email",
        help="Email address of the calling bot or user.",
    )
    group.add_option(
        f"--{prefix}config-file",
        action="store",
        dest="zulip_config_file",
        help="Location of an ini file containing the\nabove information. (default ~/.zuliprc)",
    )
    group.add_option("-v", "--verbose", action="store_true", help="Provide detailed output.")
    group.add_option(
        f"--{prefix}client",
        action="store",
        default=None,
        dest="zulip_client",
        help=optparse.SUPPRESS_HELP,
    )
    group.add_option(
        "--insecure",
        action="store_true",
        dest="insecure",
        help="""Do not verify the server certificate.
                          The https connection will not be secure.""",
    )
    group.add_option(
        "--cert-bundle",
        action="store",
        dest="cert_bundle",
        help="""Specify a file containing either the
                          server certificate, or a set of trusted
                          CA certificates. This will be used to
                          verify the server's identity. All
                          certificates should be PEM encoded.""",
    )
    group.add_option(
        "--client-cert",
        action="store",
        dest="client_cert",
        help="""Specify a file containing a client
                          certificate (not needed for most deployments).""",
    )
    group.add_option(
        "--client-cert-key",
        action="store",
        dest="client_cert_key",
        help="""Specify a file containing the client
                          certificate's key (if it is in a separate
                          file).""",
    )
    return group


def init_from_options(options: Any, client: Optional[str] = None) -> "Client":

    if getattr(options, "provision", False):
        requirements_path = os.path.abspath(os.path.join(sys.path[0], "requirements.txt"))
        try:
            import pip
        except ImportError:
            traceback.print_exc()
            print(
                "Module `pip` is not installed. To install `pip`, follow the instructions here: "
                "https://pip.pypa.io/en/stable/installing/"
            )
            sys.exit(1)
        if not pip.main(["install", "--upgrade", "--requirement", requirements_path]):
            print(
                "{color_green}You successfully provisioned the dependencies for {script}.{end_color}".format(
                    color_green="\033[92m",
                    end_color="\033[0m",
                    script=os.path.splitext(os.path.basename(sys.argv[0]))[0],
                )
            )
            sys.exit(0)

    if options.zulip_client is not None:
        client = options.zulip_client
    elif client is None:
        client = _default_client()
    return Client(
        email=options.zulip_email,
        api_key=options.zulip_api_key,
        config_file=options.zulip_config_file,
        verbose=options.verbose,
        site=options.zulip_site,
        client=client,
        cert_bundle=options.cert_bundle,
        insecure=options.insecure,
        client_cert=options.client_cert,
        client_cert_key=options.client_cert_key,
    )


def get_default_config_filename() -> Optional[str]:
    if os.environ.get("HOME") is None:
        return None

    config_file = os.path.join(os.environ["HOME"], ".zuliprc")
    if not os.path.exists(config_file) and os.path.exists(
        os.path.join(os.environ["HOME"], ".humbugrc")
    ):
        raise ZulipError(
            "The Zulip API configuration file is now ~/.zuliprc; please run:\n\n"
            "  mv ~/.humbugrc ~/.zuliprc\n"
        )
    return config_file


def validate_boolean_field(field: Optional[str]) -> Union[bool, None]:
    if not isinstance(field, str):
        return None

    field = field.lower()

    if field == "true":
        return True
    elif field == "false":
        return False
    else:
        return None


class ZulipError(Exception):
    pass


class ConfigNotFoundError(ZulipError):
    pass


class MissingURLError(ZulipError):
    pass


class UnrecoverableNetworkError(ZulipError):
    pass


class Client:
    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        config_file: Optional[str] = None,
        verbose: bool = False,
        retry_on_errors: bool = True,
        site: Optional[str] = None,
        client: Optional[str] = None,
        cert_bundle: Optional[str] = None,
        insecure: Optional[bool] = None,
        client_cert: Optional[str] = None,
        client_cert_key: Optional[str] = None,
    ) -> None:
        if client is None:
            client = _default_client()

        # Normalize user-specified path
        if config_file is not None:
            config_file = os.path.abspath(os.path.expanduser(config_file))
        # Fill values from Environment Variables if not available in Constructor
        if config_file is None:
            config_file = os.environ.get("ZULIP_CONFIG")
        if api_key is None:
            api_key = os.environ.get("ZULIP_API_KEY")
        if email is None:
            email = os.environ.get("ZULIP_EMAIL")
        if site is None:
            site = os.environ.get("ZULIP_SITE")
        if client_cert is None:
            client_cert = os.environ.get("ZULIP_CERT")
        if client_cert_key is None:
            client_cert_key = os.environ.get("ZULIP_CERT_KEY")
        if cert_bundle is None:
            cert_bundle = os.environ.get("ZULIP_CERT_BUNDLE")
        if insecure is None:
            # Be quite strict about what is accepted so that users don't
            # disable security unintentionally.
            insecure_setting = os.environ.get("ZULIP_ALLOW_INSECURE")

            if insecure_setting is not None:
                insecure = validate_boolean_field(insecure_setting)

                if insecure is None:
                    raise ZulipError(
                        "The ZULIP_ALLOW_INSECURE environment "
                        "variable is set to '{}', it must be "
                        "'true' or 'false'".format(insecure_setting)
                    )
        if config_file is None:
            config_file = get_default_config_filename()

        if config_file is not None and os.path.exists(config_file):
            config = ConfigParser()
            with open(config_file) as f:
                config.read_file(f, config_file)
            if api_key is None:
                api_key = config.get("api", "key")
            if email is None:
                email = config.get("api", "email")
            if site is None and config.has_option("api", "site"):
                site = config.get("api", "site")
            if client_cert is None and config.has_option("api", "client_cert"):
                client_cert = config.get("api", "client_cert")
            if client_cert_key is None and config.has_option("api", "client_cert_key"):
                client_cert_key = config.get("api", "client_cert_key")
            if cert_bundle is None and config.has_option("api", "cert_bundle"):
                cert_bundle = config.get("api", "cert_bundle")
            if insecure is None and config.has_option("api", "insecure"):
                # Be quite strict about what is accepted so that users don't
                # disable security unintentionally.
                insecure_setting = config.get("api", "insecure")

                insecure = validate_boolean_field(insecure_setting)

                if insecure is None:
                    raise ZulipError(
                        "insecure is set to '{}', it must be "
                        "'true' or 'false' if it is used in {}".format(
                            insecure_setting, config_file
                        )
                    )

        elif None in (api_key, email):
            raise ConfigNotFoundError(
                f"api_key or email not specified and file {config_file} does not exist"
            )

        assert api_key is not None and email is not None
        self.api_key = api_key
        self.email = email
        self.verbose = verbose
        if site is not None:
            if site.startswith("localhost"):
                site = "http://" + site
            elif not site.startswith("http"):
                site = "https://" + site
            # Remove trailing "/"s from site to simplify the below logic for adding "/api"
            site = site.rstrip("/")
            self.base_url = site
        else:
            raise MissingURLError("Missing Zulip server URL; specify via --site or ~/.zuliprc.")

        if not self.base_url.endswith("/api"):
            self.base_url += "/api"
        self.base_url += "/"
        self.retry_on_errors = retry_on_errors
        self.client_name = client

        if insecure:
            logger.warning(
                "Insecure mode enabled. The server's SSL/TLS "
                "certificate will not be validated, making the "
                "HTTPS connection potentially insecure"
            )
            self.tls_verification = False  # type: Union[bool, str]
        elif cert_bundle is not None:
            if not os.path.isfile(cert_bundle):
                raise ConfigNotFoundError(f"tls bundle '{cert_bundle}' does not exist")
            self.tls_verification = cert_bundle
        else:
            # Default behavior: verify against system CA certificates
            self.tls_verification = True

        if client_cert is None:
            if client_cert_key is not None:
                raise ConfigNotFoundError(
                    "client cert key '%s' specified, but no client cert public part provided"
                    % (client_cert_key,)
                )
        else:  # we have a client cert
            if not os.path.isfile(client_cert):
                raise ConfigNotFoundError(f"client cert '{client_cert}' does not exist")
            if client_cert_key is not None:
                if not os.path.isfile(client_cert_key):
                    raise ConfigNotFoundError(f"client cert key '{client_cert_key}' does not exist")
        self.client_cert = client_cert
        self.client_cert_key = client_cert_key

        self.session = None  # type: Optional[requests.Session]

        self.has_connected = False

        server_settings = self.get_server_settings()
        self.zulip_version: Optional[str] = server_settings.get("zulip_version")
        self.feature_level: int = server_settings.get("zulip_feature_level", 0)
        assert self.zulip_version is not None

    def ensure_session(self) -> None:

        # Check if the session has been created already, and return
        # immediately if so.
        if self.session:
            return

        # Build a client cert object for requests
        if self.client_cert_key is not None:
            assert self.client_cert is not None  # Otherwise ZulipError near end of __init__
            client_cert = (
                self.client_cert,
                self.client_cert_key,
            )  # type: Union[None, str, Tuple[str, str]]
        else:
            client_cert = self.client_cert

        # Actually construct the session
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(self.email, self.api_key)
        session.verify = self.tls_verification
        session.cert = client_cert
        session.headers.update({"User-agent": self.get_user_agent()})
        self.session = session

    def get_user_agent(self) -> str:
        vendor = ""
        vendor_version = ""
        try:
            vendor = platform.system()
            vendor_version = platform.release()
        except OSError:
            # If the calling process is handling SIGCHLD, platform.system() can
            # fail with an IOError.  See http://bugs.python.org/issue9127
            pass

        if vendor == "Linux":
            vendor, vendor_version, dummy = distro.linux_distribution()
        elif vendor == "Windows":
            vendor_version = platform.win32_ver()[1]
        elif vendor == "Darwin":
            vendor_version = platform.mac_ver()[0]

        return "{client_name} ({vendor}; {vendor_version})".format(
            client_name=self.client_name,
            vendor=vendor,
            vendor_version=vendor_version,
        )

    def do_api_query(
        self,
        orig_request: Mapping[str, Any],
        url: str,
        method: str = "POST",
        longpolling: bool = False,
        files: Optional[List[IO[Any]]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        if files is None:
            files = []

        if longpolling:
            # When long-polling, set timeout to 90 sec as a balance
            # between a low traffic rate and a still reasonable latency
            # time in case of a connection failure.
            request_timeout = 90.0
        else:
            # Otherwise, 15s should be plenty of time.
            request_timeout = 15.0 if not timeout else timeout

        request = {}
        req_files = []

        for (key, val) in orig_request.items():
            if isinstance(val, str) or isinstance(val, str):
                request[key] = val
            else:
                request[key] = json.dumps(val)

        for f in files:
            req_files.append((f.name, f))

        self.ensure_session()
        assert self.session is not None

        query_state = {
            "had_error_retry": False,
            "request": request,
            "failures": 0,
        }  # type: Dict[str, Any]

        def error_retry(error_string: str) -> bool:
            if not self.retry_on_errors or query_state["failures"] >= 10:
                return False
            if self.verbose:
                if not query_state["had_error_retry"]:
                    sys.stdout.write(
                        "zulip API(%s): connection error%s -- retrying."
                        % (
                            url.split(API_VERSTRING, 2)[0],
                            error_string,
                        )
                    )
                    query_state["had_error_retry"] = True
                else:
                    sys.stdout.write(".")
                sys.stdout.flush()
            query_state["request"]["dont_block"] = json.dumps(True)
            time.sleep(1)
            query_state["failures"] += 1
            return True

        def end_error_retry(succeeded: bool) -> None:
            if query_state["had_error_retry"] and self.verbose:
                if succeeded:
                    print("Success!")
                else:
                    print("Failed!")

        while True:
            try:
                if method == "GET":
                    kwarg = "params"
                else:
                    kwarg = "data"

                kwargs = {kwarg: query_state["request"]}

                if files:
                    kwargs["files"] = req_files

                # Actually make the request!
                res = self.session.request(
                    method,
                    urllib.parse.urljoin(self.base_url, url),
                    timeout=request_timeout,
                    **kwargs,
                )

                self.has_connected = True

                # On 50x errors, try again after a short sleep
                if str(res.status_code).startswith("5"):
                    if error_retry(f" (server {res.status_code})"):
                        continue
                    # Otherwise fall through and process the python-requests error normally
            except (requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
                # Timeouts are either a Timeout or an SSLError; we
                # want the later exception handlers to deal with any
                # non-timeout other SSLErrors
                if (
                    isinstance(e, requests.exceptions.SSLError)
                    and str(e) != "The read operation timed out"
                ):
                    raise UnrecoverableNetworkError("SSL Error")
                if longpolling:
                    # When longpolling, we expect the timeout to fire,
                    # and the correct response is to just retry
                    continue
                else:
                    end_error_retry(False)
                    raise
            except requests.exceptions.ConnectionError:
                if not self.has_connected:
                    # If we have never successfully connected to the server, don't
                    # go into retry logic, because the most likely scenario here is
                    # that somebody just hasn't started their server, or they passed
                    # in an invalid site.
                    raise UnrecoverableNetworkError("cannot connect to server " + self.base_url)

                if error_retry(""):
                    continue
                end_error_retry(False)
                raise
            except Exception:
                # We'll split this out into more cases as we encounter new bugs.
                raise

            try:
                if requests_json_is_function:
                    json_result = res.json()
                else:
                    json_result = res.json
            except Exception:
                json_result = None

            if json_result is not None:
                end_error_retry(True)
                return json_result
            end_error_retry(False)
            return {
                "msg": "Unexpected error from the server",
                "result": "http-error",
                "status_code": res.status_code,
            }

    def call_endpoint(
        self,
        url: Optional[str] = None,
        method: str = "POST",
        request: Optional[Dict[str, Any]] = None,
        longpolling: bool = False,
        files: Optional[List[IO[Any]]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        if request is None:
            request = dict()
        marshalled_request = {}
        for (k, v) in request.items():
            if v is not None:
                marshalled_request[k] = v
        versioned_url = API_VERSTRING + (url if url is not None else "")
        return self.do_api_query(
            marshalled_request,
            versioned_url,
            method=method,
            longpolling=longpolling,
            files=files,
            timeout=timeout,
        )

    def call_on_each_event(
        self,
        callback: Callable[[Dict[str, Any]], None],
        event_types: Optional[List[str]] = None,
        narrow: Optional[List[List[str]]] = None,
        **kwargs: object,
    ) -> None:
        if narrow is None:
            narrow = []

        def do_register() -> Tuple[str, int]:

            while True:
                if event_types is None:
                    res = self.register(None, None, **kwargs)
                else:
                    res = self.register(event_types, narrow, **kwargs)
                if "error" in res["result"]:
                    if self.verbose:
                        print("Server returned error:\n{}".format(res["msg"]))
                    time.sleep(1)
                else:
                    return (res["queue_id"], res["last_event_id"])

        queue_id = None
        # Make long-polling requests with `get_events`. Once a request
        # has received an answer, pass it to the callback and before
        # making a new long-polling request.
        while True:
            if queue_id is None:
                (queue_id, last_event_id) = do_register()

            try:
                res = self.get_events(queue_id=queue_id, last_event_id=last_event_id)
            except (
                requests.exceptions.Timeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
            ):
                if self.verbose:
                    print(f"Connection error fetching events:\n{traceback.format_exc()}")
                # TODO: Make this use our backoff library
                time.sleep(1)
                continue
            except Exception:
                print(f"Unexpected error:\n{traceback.format_exc()}")
                # TODO: Make this use our backoff library
                time.sleep(1)
                continue

            if "error" in res["result"]:
                if res["result"] == "http-error":
                    if self.verbose:
                        print("HTTP error fetching events -- probably a server restart")
                else:
                    if self.verbose:
                        print("Server returned error:\n{}".format(res["msg"]))
                    # Eventually, we'll only want the
                    # BAD_EVENT_QUEUE_ID check, but we check for the
                    # old string to support legacy Zulip servers.  We
                    # should remove that legacy check in 2019.
                    if res.get("code") == "BAD_EVENT_QUEUE_ID" or res["msg"].startswith(
                        "Bad event queue id:"
                    ):
                        # Our event queue went away, probably because
                        # we were asleep or the server restarted
                        # abnormally.  We may have missed some
                        # events while the network was down or
                        # something, but there's not really anything
                        # we can do about it other than resuming
                        # getting new ones.
                        #
                        # Reset queue_id to register a new event queue.
                        queue_id = None
                # Add a pause here to cover against potential bugs in this library
                # causing a DoS attack against a server when getting errors.
                # TODO: Make this back off exponentially.
                time.sleep(1)
                continue

            for event in res["events"]:
                last_event_id = max(last_event_id, int(event["id"]))
                callback(event)

    def call_on_each_message(
        self, callback: Callable[[Dict[str, Any]], None], **kwargs: object
    ) -> None:
        def event_callback(event: Dict[str, Any]) -> None:
            if event["type"] == "message":
                callback(event["message"])

        self.call_on_each_event(event_callback, ["message"], None, **kwargs)

    def get_messages(self, message_filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/get-messages for example usage
        """
        return self.call_endpoint(url="messages", method="GET", request=message_filters)

    def check_messages_match_narrow(self, **request: Dict[str, Any]) -> Dict[str, Any]:

        """
        Example usage:

        >>> client.check_messages_match_narrow(msg_ids=[11, 12],
            narrow=[{'operator': 'has', 'operand': 'link'}]
        )
        {'result': 'success', 'msg': '', 'messages': [{...}, {...}]}
        """
        return self.call_endpoint(url="messages/matches_narrow", method="GET", request=request)

    def get_raw_message(self, message_id: int) -> Dict[str, str]:
        """
        See examples/get-raw-message for example usage
        """
        return self.call_endpoint(url=f"messages/{message_id}", method="GET")

    def send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/send-message for example usage.
        """
        return self.call_endpoint(
            url="messages",
            request=message_data,
        )

    def upload_file(self, file: IO[Any]) -> Dict[str, Any]:
        """
        See examples/upload-file for example usage.
        """
        return self.call_endpoint(url="user_uploads", files=[file])

    def get_attachments(self) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_attachments()
        {'result': 'success', 'msg': '', 'attachments': [{...}, {...}]}
        """
        return self.call_endpoint(url="attachments", method="GET")

    def update_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/edit-message for example usage.
        """
        return self.call_endpoint(
            url="messages/%d" % (message_data["message_id"],),
            method="PATCH",
            request=message_data,
        )

    def delete_message(self, message_id: int) -> Dict[str, Any]:
        """
        See examples/delete-message for example usage.
        """
        return self.call_endpoint(url=f"messages/{message_id}", method="DELETE")

    def update_message_flags(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/update-flags for example usage.
        """
        return self.call_endpoint(url="messages/flags", method="POST", request=update_data)

    def mark_all_as_read(self) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.mark_all_as_read()
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="mark_all_as_read",
            method="POST",
        )

    def mark_stream_as_read(self, stream_id: int) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.mark_stream_as_read(42)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="mark_stream_as_read",
            method="POST",
            request={"stream_id": stream_id},
        )

    def mark_topic_as_read(self, stream_id: int, topic_name: str) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.mark_all_as_read(42, 'new coffee machine')
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="mark_topic_as_read",
            method="POST",
            request={
                "stream_id": stream_id,
                "topic_name": topic_name,
            },
        )

    def get_message_history(self, message_id: int) -> Dict[str, Any]:
        """
        See examples/message-history for example usage.
        """
        return self.call_endpoint(url=f"messages/{message_id}/history", method="GET")

    def add_reaction(self, reaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.add_reaction({
            'message_id': 100,
            'emoji_name': 'joy',
            'emoji_code': '1f602',
            'reaction_type': 'unicode_emoji'
        })
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="messages/{}/reactions".format(reaction_data["message_id"]),
            method="POST",
            request=reaction_data,
        )

    def remove_reaction(self, reaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.remove_reaction({
            'message_id': 100,
            'emoji_name': 'joy',
            'emoji_code': '1f602',
            'reaction_type': 'unicode_emoji'
        })
        {'msg': '', 'result': 'success'}
        """
        return self.call_endpoint(
            url="messages/{}/reactions".format(reaction_data["message_id"]),
            method="DELETE",
            request=reaction_data,
        )

    def get_realm_emoji(self) -> Dict[str, Any]:
        """
        See examples/realm-emoji for example usage.
        """
        return self.call_endpoint(url="realm/emoji", method="GET")

    def upload_custom_emoji(self, emoji_name: str, file_obj: IO[Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.upload_custom_emoji(emoji_name, file_obj)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(f"realm/emoji/{emoji_name}", method="POST", files=[file_obj])

    def delete_custom_emoji(self, emoji_name: str) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.delete_custom_emoji("green_tick")
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"realm/emoji/{emoji_name}",
            method="DELETE",
        )

    def get_realm_linkifiers(self) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_realm_linkifiers()
        {
            'result': 'success',
            'msg': '',
            'linkifiers': [
                {
                    'id': 1,
                    'pattern': #(?P<id>[0-9]+)',
                    'url_format': 'https://github.com/zulip/zulip/issues/%(id)s',
                },
            ]
        }
        """
        return self.call_endpoint(
            url="realm/linkifiers",
            method="GET",
        )

    def add_realm_filter(self, pattern: str, url_format_string: str) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.add_realm_filter('#(?P<id>[0-9]+)', 'https://github.com/zulip/zulip/issues/%(id)s')
        {'result': 'success', 'msg': '', 'id': 42}
        """
        return self.call_endpoint(
            url="realm/filters",
            method="POST",
            request={
                "pattern": pattern,
                "url_format_string": url_format_string,
            },
        )

    def remove_realm_filter(self, filter_id: int) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.remove_realm_filter(42)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"realm/filters/{filter_id}",
            method="DELETE",
        )

    def get_realm_profile_fields(self) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_realm_profile_fields()
        {'result': 'success', 'msg': '', 'custom_fields': [{...}, {...}, {...}, {...}]}
        """
        return self.call_endpoint(
            url="realm/profile_fields",
            method="GET",
        )

    def create_realm_profile_field(self, **request: Any) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.create_realm_profile_field(name='Phone', hint='Contact No.', field_type=1)
        {'result': 'success', 'msg': '', 'id': 9}
        """
        return self.call_endpoint(
            url="realm/profile_fields",
            method="POST",
            request=request,
        )

    def remove_realm_profile_field(self, field_id: int) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.remove_realm_profile_field(field_id=9)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"realm/profile_fields/{field_id}",
            method="DELETE",
        )

    def reorder_realm_profile_fields(self, **request: Any) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.reorder_realm_profile_fields(order=[8, 7, 6, 5, 4, 3, 2, 1])
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="realm/profile_fields",
            method="PATCH",
            request=request,
        )

    def update_realm_profile_field(self, field_id: int, **request: Any) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_realm_profile_field(field_id=1, name='Email')
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"realm/profile_fields/{field_id}",
            method="PATCH",
            request=request,
        )

    def get_server_settings(self) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_server_settings()
        {'msg': '', 'result': 'success', 'zulip_version': '1.9.0', 'push_notifications_enabled': False, ...}
        """
        return self.call_endpoint(
            url="server_settings",
            method="GET",
        )

    def get_events(self, **request: Any) -> Dict[str, Any]:
        """
        See the register() method for example usage.
        """
        return self.call_endpoint(
            url="events",
            method="GET",
            longpolling=True,
            request=request,
        )

    def register(
        self,
        event_types: Optional[Iterable[str]] = None,
        narrow: Optional[List[List[str]]] = None,
        **kwargs: object,
    ) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.register(['message'])
        {u'msg': u'', u'max_message_id': 112, u'last_event_id': -1, u'result': u'success', u'queue_id': u'1482093786:2'}
        >>> client.get_events(queue_id='1482093786:2', last_event_id=0)
        {...}
        """

        if narrow is None:
            narrow = []

        request = dict(event_types=event_types, narrow=narrow, **kwargs)

        return self.call_endpoint(
            url="register",
            request=request,
        )

    def deregister(self, queue_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.register(['message'])
        {u'msg': u'', u'max_message_id': 113, u'last_event_id': -1, u'result': u'success', u'queue_id': u'1482093786:3'}
        >>> client.deregister('1482093786:3')
        {u'msg': u'', u'result': u'success'}
        """
        request = dict(queue_id=queue_id)

        return self.call_endpoint(
            url="events",
            method="DELETE",
            request=request,
            timeout=timeout,
        )

    def get_profile(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_profile()
        {u'user_id': 5, u'full_name': u'Iago', u'short_name': u'iago', ...}
        """
        return self.call_endpoint(
            url="users/me",
            method="GET",
            request=request,
        )

    def get_user_presence(self, email: str) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_user_presence('iago@zulip.com')
        {'presence': {'website': {'timestamp': 1486799122, 'status': 'active'}}, 'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"users/{email}/presence",
            method="GET",
        )

    def get_realm_presence(self) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_realm_presence()
        {'presences': {...}, 'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="realm/presence",
            method="GET",
        )

    def update_presence(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_presence({
                status='active',
                ping_only=False,
                new_user_input=False,
            })
            {'result': 'success', 'server_timestamp': 1333649180.7073195, 'presences': {'iago@zulip.com': { ... }}, 'msg': ''}
        """
        return self.call_endpoint(
            url="users/me/presence",
            method="POST",
            request=request,
        )

    def get_streams(self, **request: Any) -> Dict[str, Any]:
        """
        See examples/get-public-streams for example usage.
        """
        return self.call_endpoint(
            url="streams",
            method="GET",
            request=request,
        )

    def update_stream(self, stream_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/edit-stream for example usage.
        """

        return self.call_endpoint(
            url="streams/{}".format(stream_data["stream_id"]),
            method="PATCH",
            request=stream_data,
        )

    def delete_stream(self, stream_id: int) -> Dict[str, Any]:
        """
        See examples/delete-stream for example usage.
        """
        return self.call_endpoint(
            url=f"streams/{stream_id}",
            method="DELETE",
        )

    def add_default_stream(self, stream_id: int) -> Dict[str, Any]:

        """
        Example usage:

        >>> client.add_default_stream(5)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="default_streams",
            method="POST",
            request={"stream_id": stream_id},
        )

    def get_user_by_id(self, user_id: int, **request: Any) -> Dict[str, Any]:

        """
        Example usage:

        >>> client.get_user_by_id(8, include_custom_profile_fields=True)
        {'result': 'success', 'msg': '', 'user': [{...}, {...}]}
        """
        return self.call_endpoint(
            url=f"users/{user_id}",
            method="GET",
            request=request,
        )

    def deactivate_user_by_id(self, user_id: int) -> Dict[str, Any]:

        """
        Example usage:

        >>> client.deactivate_user_by_id(8)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"users/{user_id}",
            method="DELETE",
        )

    def reactivate_user_by_id(self, user_id: int) -> Dict[str, Any]:

        """
        Example usage:

        >>> client.reactivate_user_by_id(8)
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url=f"users/{user_id}/reactivate",
            method="POST",
        )

    def update_user_by_id(self, user_id: int, **request: Any) -> Dict[str, Any]:

        """
        Example usage:

        >>> client.update_user_by_id(8, full_name="New Name")
        {'result': 'success', 'msg': ''}
        """

        if "full_name" in request and self.feature_level < 106:
            # As noted in https://github.com/zulip/zulip/issues/18409,
            # before feature level 106, the server expected a
            # buggy double JSON encoding of the `full_name` parameter.
            request["full_name"] = json.dumps(request["full_name"])

        return self.call_endpoint(url=f"users/{user_id}", method="PATCH", request=request)

    def get_users(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        See examples/list-users for example usage.
        """
        return self.call_endpoint(
            url="users",
            method="GET",
            request=request,
        )

    def get_members(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # This exists for backwards-compatibility; we renamed this
        # function get_users for consistency with the rest of the API.
        # Later, we may want to add a warning for clients using this
        # legacy name.
        return self.get_users(request=request)

    def get_alert_words(self) -> Dict[str, Any]:
        """
        See examples/alert-words for example usage.
        """
        return self.call_endpoint(url="users/me/alert_words", method="GET")

    def add_alert_words(self, alert_words: List[str]) -> Dict[str, Any]:
        """
        See examples/alert-words for example usage.
        """
        return self.call_endpoint(
            url="users/me/alert_words", method="POST", request={"alert_words": alert_words}
        )

    def remove_alert_words(self, alert_words: List[str]) -> Dict[str, Any]:
        """
        See examples/alert-words for example usage.
        """
        return self.call_endpoint(
            url="users/me/alert_words", method="DELETE", request={"alert_words": alert_words}
        )

    def get_subscriptions(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        See examples/get-subscriptions for example usage.
        """
        return self.call_endpoint(
            url="users/me/subscriptions",
            method="GET",
            request=request,
        )

    def list_subscriptions(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.warning(
            "list_subscriptions() is deprecated." " Please use get_subscriptions() instead."
        )
        return self.get_subscriptions(request)

    def add_subscriptions(self, streams: Iterable[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """
        See examples/subscribe for example usage.
        """
        request = dict(subscriptions=streams, **kwargs)

        return self.call_endpoint(
            url="users/me/subscriptions",
            request=request,
        )

    def remove_subscriptions(
        self,
        streams: Iterable[str],
        principals: Optional[Union[Sequence[str], Sequence[int]]] = None,
    ) -> Dict[str, Any]:
        """
        See examples/unsubscribe for example usage.
        """
        request: Dict[str, object] = dict(subscriptions=streams)
        if principals is not None:
            request["principals"] = principals
        return self.call_endpoint(
            url="users/me/subscriptions",
            method="DELETE",
            request=request,
        )

    def get_subscription_status(self, user_id: int, stream_id: int) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.get_subscription_status(user_id=7, stream_id=1)
        {'result': 'success', 'msg': '', 'is_subscribed': False}
        """
        return self.call_endpoint(
            url=f"users/{user_id}/subscriptions/{stream_id}",
            method="GET",
        )

    def mute_topic(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        See examples/mute-topic for example usage.
        """
        return self.call_endpoint(
            url="users/me/subscriptions/muted_topics", method="PATCH", request=request
        )

    def update_subscription_settings(
        self, subscription_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_subscription_settings([{
            'stream_id': 1,
            'property': 'pin_to_top',
            'value': True
        },
        {
            'stream_id': 3,
            'property': 'color',
            'value': 'f00'
        }])
        {'result': 'success', 'msg': '', 'subscription_data': [{...}, {...}]}
        """
        return self.call_endpoint(
            url="users/me/subscriptions/properties",
            method="POST",
            request={"subscription_data": subscription_data},
        )

    def update_notification_settings(self, notification_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_notification_settings({
            'enable_stream_push_notifications': True,
            'enable_offline_push_notifications': False,
        })
        {'enable_offline_push_notifications': False, 'enable_stream_push_notifications': True, 'msg': '', 'result': 'success'}
        """
        return self.call_endpoint(
            url="settings/notifications",
            method="PATCH",
            request=notification_settings,
        )

    def get_stream_id(self, stream: str) -> Dict[str, Any]:
        """
        Example usage: client.get_stream_id('devel')
        """
        stream_encoded = urllib.parse.quote(stream, safe="")
        url = f"get_stream_id?stream={stream_encoded}"
        return self.call_endpoint(
            url=url,
            method="GET",
            request=None,
        )

    def get_stream_topics(self, stream_id: int) -> Dict[str, Any]:
        """
        See examples/get-stream-topics for example usage.
        """
        return self.call_endpoint(url=f"users/me/{stream_id}/topics", method="GET")

    def get_user_groups(self) -> Dict[str, Any]:
        """
        Example usage:
        >>> client.get_user_groups()
        {'result': 'success', 'msg': '', 'user_groups': [{...}, {...}]}
        """
        return self.call_endpoint(
            url="user_groups",
            method="GET",
        )

    def create_user_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:
        >>> client.create_user_group({
            'name': 'marketing',
            'description': "Members of ACME Corp.'s marketing team.",
            'members': [4, 8, 15, 16, 23, 42],
        })
        {'msg': '', 'result': 'success'}
        """
        return self.call_endpoint(
            url="user_groups/create",
            method="POST",
            request=group_data,
        )

    def update_user_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_user_group({
            'group_id': 1,
            'name': 'marketing',
            'description': "Members of ACME Corp.'s marketing team.",
        })
        {'description': 'Description successfully updated.', 'name': 'Name successfully updated.', 'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(
            url="user_groups/{}".format(group_data["group_id"]),
            method="PATCH",
            request=group_data,
        )

    def remove_user_group(self, group_id: int) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.remove_user_group(42)
        {'msg': '', 'result': 'success'}
        """
        return self.call_endpoint(
            url=f"user_groups/{group_id}",
            method="DELETE",
        )

    def update_user_group_members(
        self, user_group_id: int, group_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_user_group_members(1, {
            'delete': [8, 10],
            'add': [11],
        })
        {'msg': '', 'result': 'success'}
        """
        return self.call_endpoint(
            url=f"user_groups/{user_group_id}/members",
            method="POST",
            request=group_data,
        )

    def get_subscribers(self, **request: Any) -> Dict[str, Any]:
        """
        Example usage: client.get_subscribers(stream='devel')
        """
        response = self.get_stream_id(request["stream"])
        if response["result"] == "error":
            return response

        stream_id = response["stream_id"]
        url = "streams/%d/members" % (stream_id,)
        return self.call_endpoint(
            url=url,
            method="GET",
            request=request,
        )

    def render_message(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.render_message(request=dict(content='foo **bar**'))
        {u'msg': u'', u'rendered': u'<p>foo <strong>bar</strong></p>', u'result': u'success'}
        """
        return self.call_endpoint(
            url="messages/render",
            method="POST",
            request=request,
        )

    def create_user(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        See examples/create-user for example usage.
        """
        return self.call_endpoint(
            method="POST",
            url="users",
            request=request,
        )

    def update_storage(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_storage({'storage': {"entry 1": "value 1", "entry 2": "value 2", "entry 3": "value 3"}})
        >>> client.get_storage({'keys': ["entry 1", "entry 3"]})
        {'result': 'success', 'storage': {'entry 1': 'value 1', 'entry 3': 'value 3'}, 'msg': ''}
        """
        return self.call_endpoint(
            url="bot_storage",
            method="PUT",
            request=request,
        )

    def get_storage(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Example usage:

        >>> client.update_storage({'storage': {"entry 1": "value 1", "entry 2": "value 2", "entry 3": "value 3"}})
        >>> client.get_storage()
        {'result': 'success', 'storage': {"entry 1": "value 1", "entry 2": "value 2", "entry 3": "value 3"}, 'msg': ''}
        >>> client.get_storage({'keys': ["entry 1", "entry 3"]})
        {'result': 'success', 'storage': {'entry 1': 'value 1', 'entry 3': 'value 3'}, 'msg': ''}
        """
        return self.call_endpoint(
            url="bot_storage",
            method="GET",
            request=request,
        )

    def set_typing_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example usage:
        >>> client.set_typing_status({
            'op': 'start',
            'to': [9, 10],
        })
        {'result': 'success', 'msg': ''}
        """
        return self.call_endpoint(url="typing", method="POST", request=request)

    def move_topic(
        self,
        stream: str,
        new_stream: str,
        topic: str,
        new_topic: Optional[str] = None,
        message_id: Optional[int] = None,
        propagate_mode: EditPropagateMode = "change_all",
        notify_old_topic: bool = True,
        notify_new_topic: bool = True,
    ) -> Dict[str, Any]:
        """
        Move a topic from ``stream`` to ``new_stream``

        The topic will be renamed if ``new_topic`` is provided.
        message_id and propagation_mode let you control which messages
        should be moved. The default behavior moves all messages in topic.

        propagation_mode must be one of: `change_one`, `change_later`,
        `change_all`. Defaults to `change_all`.

        Example usage:

        >>> client.move_topic('stream_a', 'stream_b', 'my_topic')
        {'result': 'success', 'msg': ''}
        """
        # get IDs for source and target streams
        result = self.get_stream_id(stream)
        if result["result"] != "success":
            return result
        stream = result["stream_id"]

        result = self.get_stream_id(new_stream)
        if result["result"] != "success":
            return result
        new_stream = result["stream_id"]

        if message_id is None:
            if propagate_mode != "change_all":
                raise AttributeError(
                    "A message_id must be provided if " 'propagate_mode isn\'t "change_all"'
                )

            # ask the server for the latest message ID in the topic.
            result = self.get_messages(
                {
                    "anchor": "newest",
                    "narrow": [
                        {"operator": "stream", "operand": stream},
                        {"operator": "topic", "operand": topic},
                    ],
                    "num_before": 1,
                    "num_after": 0,
                }
            )

            if result["result"] != "success":
                return result

            if len(result["messages"]) <= 0:
                return {"result": "error", "msg": f'No messages found in topic: "{topic}"'}

            message_id = result["messages"][0]["id"]

        # move topic containing message to new stream
        request = {
            "stream_id": new_stream,
            "propagate_mode": propagate_mode,
            "topic": new_topic,
            "send_notification_to_old_thread": notify_old_topic,
            "send_notification_to_new_thread": notify_new_topic,
        }
        return self.call_endpoint(
            url=f"messages/{message_id}",
            method="PATCH",
            request=request,
        )


class ZulipStream:
    """
    A Zulip stream-like object
    """

    def __init__(self, type: str, to: str, subject: str, **kwargs: Any) -> None:
        self.client = Client(**kwargs)
        self.type = type
        self.to = to
        self.subject = subject

    def write(self, content: str) -> None:
        message = {"type": self.type, "to": self.to, "subject": self.subject, "content": content}
        self.client.send_message(message)

    def flush(self) -> None:
        pass


def hash_util_decode(string: str) -> str:
    """
    Returns a decoded string given a hash_util_encode() [present in zulip/zulip's zerver/lib/url_encoding.py] encoded string.

    Example usage:
    >>> zulip.hash_util_decode('test.20here')
    'test here'
    """
    # Acknowledge custom string replacements in zulip/zulip's zerver/lib/url_encoding.py before unquoting.
    # NOTE: urllib.parse.unquote already does .replace('%2E', '.').
    return urllib.parse.unquote(string.replace(".", "%"))


########################################################################
# The below hackery is designed to allow running the Zulip's automated
# tests for its API documentation from old server versions against
# python-zulip-api.  Generally, we expect those tests to be a way to
# validate that the Python bindings work correctly against old server
# versions.
#
# However, in cases where we've changed the interface of the Python
# bindings since the release of the relevant server version, such
# tests will fail, which is an artifact of the fact that the
# documentation that comes with that old server release is
# inconsistent with this library.
#
# The following logic is designed to work around that problem so that
# we can verify that you can use the latest version of the Python
# bindings with any server version (even if you have to read the
# current API documentation).
LEGACY_CLIENT_INTERFACE_FROM_SERVER_DOCS_VERSION = os.environ.get(
    "LEGACY_CLIENT_INTERFACE_FROM_SERVER_DOCS_VERSION"
)

if LEGACY_CLIENT_INTERFACE_FROM_SERVER_DOCS_VERSION == "3":
    # This block is support for testing Zulip 3.x, which documents old
    # interfaces for the following functions:
    class LegacyInterfaceClient(Client):
        def update_user_group_members(self, group_data: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore # Intentional override; see comments above.
            modern_group_data = group_data.copy()
            group_id = group_data["group_id"]
            del modern_group_data["group_id"]
            return super().update_user_group_members(group_id, modern_group_data)

        def get_realm_filters(self) -> Dict[str, Any]:
            """
            Example usage:

            >>> client.get_realm_filters()
            {'result': 'success', 'msg': '', 'filters': [['#(?P<id>[0-9]+)', 'https://github.com/zulip/zulip/issues/%(id)s', 1]]}
            """
            # This interface was removed in 4d482e0ef30297f716885fd8246f4638a856ba3b
            return self.call_endpoint(
                url="realm/filters",
                method="GET",
            )

    Client = LegacyInterfaceClient  # type: ignore # Intentional override; see comments above.
