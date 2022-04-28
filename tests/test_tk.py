from unittest import TestCase
from nrrd_twitch_bot.lib.tk import TwitchBotLogApp
from tkinter import Text
from logging import Logger
from asyncio import PriorityQueue, AbstractEventLoop


class TestTwitchBotLogApp(TestCase):

    # this will run on a separate thread.
    async def _start_app(self):
        self.app.mainloop()

    def setUp(self):
        self.app = TwitchBotLogApp(False)
        self._start_app()

    def tearDown(self):
        self.app.destroy()

    def test_startup(self):
        title = self.app.winfo_toplevel().title()
        expected = 'Twitch Bot Log'
        self.assertEqual(title, expected)

    def test_log_txt(self):
        self.assertIsInstance(self.app.bot_log, Text)

    def test_logger(self):
        self.assertIsInstance(self.app.logger, Logger)

    def test_loop(self):
        self.assertIsInstance(self.app.loop, AbstractEventLoop)

    def test_queue(self):
        self.assertIsInstance(self.app.shutdown_queue, PriorityQueue)
