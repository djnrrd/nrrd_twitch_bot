""""The TK application for the Twitch bot log handler
"""
import tkinter as tk
from tkinter import font as tk_font
from tkinter import scrolledtext


class TwitchBotLogApp(tk.Tk):
    """The main app window for the Twitch bot log

    :param kwargs: List of keyword arguments for a Tk applications
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Main App Setup
        self.title('Twitch Bot Log')
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        self.geometry('800x360')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Main frame setup
        self.main_frame = LogFrame(self)
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        # Set a top level reference to the scrolling text widget
        # The widget creates a frame with a default name
        bot_log_path = 'log_frame.!frame.bot_log_txt'
        self.bot_log = self.nametowidget(bot_log_path)


class LogFrame(tk.Frame):
    """The main frame for the Twitch bot log

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='log_frame', *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._make_scrolled_txt()

    def _make_scrolled_txt(self) -> None:
        """Create the scrolled text area to be used for the log
        """
        st = scrolledtext.ScrolledText(self, state='disabled',
                                       name='bot_log_txt', bg='DarkGray')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=0, sticky='nsew')
