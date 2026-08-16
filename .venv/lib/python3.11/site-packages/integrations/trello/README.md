# A script that automates setting up a webhook with Trello

Usage :

1. Make sure you have all of the relevant Trello credentials before
   executing the script:

    - The Trello API KEY
    - The Trello TOKEN
    - The Zulip webhook URL
    - Trello board name
    - Trello board ID

2. Execute the script :

    $ python zulip_trello.py --trello-board-name <trello_board_name> \
                             --trello-board-id   <trello_board_id> \
                             --trello-api-key  <trello_api_key> \
                             --trello-token <trello_token> \
                             --zulip-webhook-url <zulip_webhook_url>

For more information, please see Zulip's documentation on how to set up
a Trello integration [here](https://zulip.com/integrations/doc/trello).
