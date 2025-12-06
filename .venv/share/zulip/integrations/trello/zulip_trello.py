#!/usr/bin/env python3
#
# An easy Trello integration for Zulip.


import argparse
import sys

try:
    import requests
except ImportError:
    print("Error: Please install the python requests library before running this script:")
    print("http://docs.python-requests.org/en/master/user/install/")
    sys.exit(1)


def get_model_id(options):
    """get_model_id

    Get Model Id from Trello API

    :options: argparse.Namespace arguments

    :returns: str id_model Trello board idModel

    """

    trello_api_url = f"https://api.trello.com/1/board/{options.trello_board_id}"

    params = {
        "key": options.trello_api_key,
        "token": options.trello_token,
    }

    trello_response = requests.get(trello_api_url, params=params)

    if trello_response.status_code != 200:
        print("Error: Can't get the idModel. Please check the configuration")
        sys.exit(1)

    board_info_json = trello_response.json()

    return board_info_json["id"]


def get_webhook_id(options, id_model):
    """get_webhook_id

    Get webhook id from Trello API

    :options: argparse.Namespace arguments
    :id_model: str Trello board idModel

    :returns: str id_webhook Trello webhook id

    """

    trello_api_url = "https://api.trello.com/1/webhooks/"

    data = {
        "key": options.trello_api_key,
        "token": options.trello_token,
        "description": "Webhook for Zulip integration (From Trello {} to Zulip)".format(
            options.trello_board_name,
        ),
        "callbackURL": options.zulip_webhook_url,
        "idModel": id_model,
    }

    trello_response = requests.post(trello_api_url, data=data)

    if trello_response.status_code != 200:
        print("Error: Can't create the Webhook:", trello_response.text)
        sys.exit(1)

    webhook_info_json = trello_response.json()

    return webhook_info_json["id"]


def create_webhook(options):
    """create_webhook

    Create Trello webhook

    :options: argparse.Namespace arguments

    """

    # first, we need to get the idModel
    print(f"Getting Trello idModel for the {options.trello_board_name} board...")

    id_model = get_model_id(options)

    if id_model:
        print("Success! The idModel is", id_model)

    id_webhook = get_webhook_id(options, id_model)

    if id_webhook:
        print("Success! The webhook ID is", id_webhook)

    print(
        "Success! The webhook for the {} Trello board was successfully created.".format(
            options.trello_board_name
        )
    )


def main():
    description = """
zulip_trello.py is a handy little script that allows Zulip users to
quickly set up a Trello webhook.

Note: The Trello webhook instructions available on your Zulip server
may be outdated. Please make sure you follow the updated instructions
at <https://zulip.com/integrations/doc/trello>.
"""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--trello-board-name", required=True, help="The Trello board name.")
    parser.add_argument(
        "--trello-board-id",
        required=True,
        help=("The Trello board short ID. Can usually be found " "in the URL of the Trello board."),
    )
    parser.add_argument(
        "--trello-api-key",
        required=True,
        help=(
            "Visit https://trello.com/1/appkey/generate to generate "
            "an APPLICATION_KEY (need to be logged into Trello)."
        ),
    )
    parser.add_argument(
        "--trello-token",
        required=True,
        help=(
            "Visit https://trello.com/1/appkey/generate and under "
            "`Developer API Keys`, click on `Token` and generate "
            "a Trello access token."
        ),
    )
    parser.add_argument(
        "--zulip-webhook-url", required=True, help="The webhook URL that Trello will query."
    )

    options = parser.parse_args()
    create_webhook(options)


if __name__ == "__main__":
    main()
