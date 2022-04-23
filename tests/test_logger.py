from unittest import TestCase
import _tkinter
from logging import Logger, DEBUG, INFO
from datetime import datetime
from nrrd_twitch_bot.lib.tk import TwitchBotLogApp
from nrrd_twitch_bot.lib.logger import setup_logger


class TestTwitchBotLoggerDebug(TestCase):

    # this will run on a separate thread.
    async def _start_app(self):
        self.app.mainloop()

    def setUp(self):
        self.app = TwitchBotLogApp()
        self.pump_events()
        self.logger = setup_logger(self.app, debug=True)
        self._start_app()

    def tearDown(self):
        self.app.destroy()
        self.pump_events()

    def pump_events(self):
        while self.app.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass

    def test_logger(self):
        self.assertIsInstance(self.logger, Logger)

    def test_level(self):
        self.assertEqual(self.logger.level, DEBUG)

    def test_if_handlers(self):
        self.assertTrue(self.logger.hasHandlers())

    def test_handlers(self):
        self.pump_events()
        time_str = datetime.now().strftime('%H:%M:%S')
        self.logger.debug('Debug message')
        self.logger.info('Info message')
        self.logger.warning('Warning message')
        self.pump_events()
        log_txt = self.app.bot_log.get('1.0', 'end-1c')
        self.pump_events()
        expect_txt = f"DEBUG - {time_str} - Debug message\n" \
                     f"INFO - {time_str} - Info message\n" \
                     f"WARNING - {time_str} - Warning message\n"
        self.assertEqual(expect_txt, log_txt)


class TestTwitchBotLoggerInfo(TestCase):

    # this will run on a separate thread.
    async def _start_app(self):
        self.app.mainloop()

    def setUp(self):
        self.app = TwitchBotLogApp()
        self.pump_events()
        self.logger = setup_logger(self.app)
        self._start_app()

    def tearDown(self):
        self.app.destroy()
        self.pump_events()

    def pump_events(self):
        while self.app.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass

    def test_logger(self):
        self.assertIsInstance(self.logger, Logger)

    def test_level(self):
        self.assertEqual(self.logger.level, INFO)

    def test_if_handlers(self):
        self.assertTrue(self.logger.hasHandlers())

    def test_handlers(self):
        self.pump_events()
        time_str = datetime.now().strftime('%H:%M:%S')
        self.logger.debug('Debug message')
        self.logger.info('Info message')
        self.logger.warning('Warning message')
        self.pump_events()
        log_txt = self.app.bot_log.get('1.0', 'end-1c')
        self.pump_events()
        expect_txt = f"INFO - {time_str} - Info message\n" \
                     f"WARNING - {time_str} - Warning message\n"
        self.assertEqual(expect_txt, log_txt)
