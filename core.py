import zulip
import urwid

from helper import async
from model import ZulipModel
from ui import ZulipView

class ZulipController:
    """
    A class responsible for setting up the model and view and running
    the application.
    """

    def __init__(self, config_file: str) -> None:
        self.client = zulip.Client(config_file=config_file)
        self.model = ZulipModel(self)
        self.view = ZulipView(self)

    @async
    def update(self) -> None:
        self.client.call_on_each_message(self.model.update_messages)

    def main(self) -> None:
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.update()
        self.loop.run()
