"""A module for setting up the logger and custom TK Scrolled Text log handler
"""
from typing import Type, TYPE_CHECKING, Union
import pathlib
import logging
from tkinter import END, Text
from datetime import datetime
if TYPE_CHECKING:
    from .tk import TwitchBotLogApp


def setup_logger(debug: bool = False,
                 app: Union['TwitchBotLogApp', None] = None,
                 file_path: Union[Type[pathlib.Path], None] = None) \
        -> logging.Logger:
    """Set up the logger for the application optionally using the tkinter
    scrolling text box for the logs

    :param debug: If debug messages should be logged
    :param app: The tkinter application
    :param file_path:
    :return: A Logger object
    """
    log_fmt = logging.Formatter('%(levelname)s - %(message)s')
    logger = logging.getLogger('twitch_bot')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_fmt)
    logger.addHandler(console_handler)
    if app:
        text_handler = TkTextHandler(app.bot_log)
        logger.addHandler(text_handler)
    if file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(log_fmt)
        logger.addHandler(file_handler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


class TkTextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget
    Adapted from Moshe Kaplan:
    https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    :param tk_widget: Tkinter scrolled text widget to write to
    """

    def __init__(self, tk_widget: Text, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Store a reference to the scrolled Text it will log to
        self.tk_widget = tk_widget

    def emit(self, record) -> None:
        """Override the normal Handler emit method to write to a tkinter
        scrolled text widget

        :param record: The log record
        """
        def append() -> None:
            """Nested function to call in the program loop
            """
            msg = self.format(record)
            self.tk_widget.configure(state='normal')
            if record.levelname in ('INFO', 'DEBUG'):
                self.tk_widget.insert(END, f"{record.levelname}", 'green_level')
            else:
                self.tk_widget.insert(END, f"{record.levelname}", 'red_level')
            self.tk_widget.insert(END, f" - "
                                       f"{datetime.now().strftime('%H:%M:%S')}"
                                       f" - ", 'time')
            self.tk_widget.insert(END, f"{msg}\n", 'message')

            self.tk_widget.tag_config('green_level', foreground='green')
            self.tk_widget.tag_config('red_level', foreground='red')
            self.tk_widget.configure(state='disabled')
            # Autoscroll to the bottom
            self.tk_widget.yview(END)
        # This is necessary because we can't modify the Text from other
        # threads, we have to add it to the loop
        self.tk_widget.after(0, append)
