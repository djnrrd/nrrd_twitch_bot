""""The TK application for the Twitch bot log handler
"""
from typing import Type, Union
import pathlib
from configparser import ConfigParser
from logging import Logger
import asyncio
import tkinter as tk
from tkinter import font as tk_font
from tkinter import scrolledtext
from nrrd_twitch_bot.lib.logger import setup_logger
from nrrd_twitch_bot.lib.config import load_config, save_config
from nrrd_twitch_bot.lib.twitch_oauth import get_twitch_oauth_token
from nrrd_twitch_bot.run import start_new_thread


class TwitchBotLogApp(tk.Tk):
    """The main app window for the Twitch bot log

    :param debug: If the logger should run in debug mode
    :param kwargs: List of keyword arguments for a Tk applications
    """
    def __init__(self, debug: bool,
                 log_file_path: Union[Type[pathlib.Path], None],
                 *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # This custom property is required for the TK app setup
        self.run_services = tk.BooleanVar(value=False)
        # Setup the TK app
        self._setup_app()
        # Shortcut to the log widget
        self.bot_log = self.nametowidget('log_frame.!frame.bot_log_txt')
        # Start the logger
        self.logger = setup_logger(debug, self, log_file_path)
        # Create the asyncio event loop and shutdown message queue
        self.loop = asyncio.new_event_loop()
        self.shutdown_queue = asyncio.PriorityQueue()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        # Main App Setup
        self.title('Twitch Bot Log')
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        self.geometry('800x360')
        # Make the X button run something other that destroy()
        self.protocol('WM_DELETE_WINDOW', self.close_app)
        # App grid setup
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Main frame setup
        main_frame = LogFrame(self)
        main_frame.grid(row=0, column=0, sticky='nsew')
        # Menu bar setup
        self.config(menu=self._build_menu())

    def _build_menu(self) -> tk.Menu:
        """Build the main application menu

        :return: the application menu
        """
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Options...", command=self.launch_options)
        file_menu.add_command(label="Exit", command=self.close_app)
        menu_bar.add_cascade(label="File", menu=file_menu)
        run_menu = tk.Menu(menu_bar, tearoff=0)
        run_menu.add_checkbutton(label="Start/Stop Services",
                                 command=self.start_stop_sockets,
                                 variable=self.run_services, onvalue=1,
                                 offvalue=0)
        menu_bar.add_cascade(label="Run", menu=run_menu)
        return menu_bar

    def launch_options(self) -> None:
        """Launch the options window
        """
        OptionsWindow(self)

    def start_stop_sockets(self) -> None:
        """Toggle running the Websockets clients and servers via the Run menu
        """
        # The function is called AFTER the variable is set by the menu
        # checkbutton, so this looks ass backwards
        if self.run_services.get():
            self.launch_sockets()
        else:
            self.shutdown_sockets()

    def launch_sockets(self) -> None:
        """Launch the websocket clients and servers in a thread
        """
        self.logger.info('tk.py: Starting services in new thread')
        start_new_thread(self.logger, self.loop, self.shutdown_queue)

    def shutdown_sockets(self) -> None:
        """Gracefully shutdown the websocket clients and servers
        """
        self.logger.info('tk.py: Shutting down services')
        self.shutdown_queue.put_nowait((0, 'SHUTDOWN'))
        while self.loop.is_running():
            self.update()
        self.logger.debug('tk.py: self.loop no longer running')

    def close_app(self) -> None:
        """Gracefully shutdown the websocket clients and servers before
        closing the tkinter app
        """
        if self.run_services:
            self.shutdown_sockets()
        self.destroy()


class LogFrame(tk.Frame):
    """The main frame for the Twitch bot log

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='log_frame', *args, **kwargs)
        self._setup_app()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._make_scrolled_txt()

    def _make_scrolled_txt(self) -> None:
        """Create the scrolled text area to be used for the log
        """
        scroll_txt = scrolledtext.ScrolledText(self, state='disabled',
                                               name='bot_log_txt',
                                               bg='DarkGray')
        scroll_txt.configure(font='TkFixedFont')
        scroll_txt.grid(column=0, row=0, sticky='nsew')


class OptionsWindow(tk.Toplevel):
    """The options window for the Twitch bot log

    :param kwargs: List of keyword arguments for a Tk applications
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='options', *args, **kwargs)
        self._setup_app()
        # Paths to widgets
        self.options_list = \
            self.nametowidget('options_frame.options_list.option_list_lbx')
        self.options_action = \
            self.nametowidget('options_frame.options_action')
        self._load_options_list()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        self.title('Twitch Bot Log - Options')
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        self.geometry('800x360')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Main frame setup
        main_frame = OptionsFrame(self)
        main_frame.grid(row=0, column=0, sticky='nsew')

    def _load_options_list(self) -> None:
        """Load the options categories in the list box
        """
        self.options_list.insert('end', 'Twitch Login')
        self.options_list.insert('end', 'Test Option')

    def options_select(self, event: tk.Event) -> None:
        """Load the options section for the selected option

        :param event: The Tkinter <<ListboxSelect>> event
        """
        logger = self.master.logger
        idx = event.widget.curselection()
        option = event.widget.get(idx)
        if option == 'Twitch Login':
            option_frame = TwitchLogin(logger, self.options_action)
        elif option == 'Test Option':
            option_frame = TestOption(self.options_action)
        else:
            option_frame = tk.Frame()
        option_frame.grid(column=0, row=0, sticky='nsew')


class OptionsFrame(tk.Frame):
    """The main frame for the Twitch bot options window

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='options_frame', *args, **kwargs)
        self._setup_app()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=9)
        option_list = OptionsList(self)
        doc_action = OptionsActions(self)
        option_list.grid(column=0, row=0, sticky='nsew')
        doc_action.grid(row=0, column=1, sticky='nsew')


class OptionsList(tk.Frame):
    """The frame for the Twitch bot options list

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='options_list', *args, **kwargs)
        self._setup_app()
        self._make_list_box()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1)

    def _make_list_box(self) -> None:
        """Create the scrolling list box
        """
        list_box = tk.Listbox(self, selectmode='single', name='option_list_lbx')
        list_box.grid(row=0, column=0, sticky='nsew')
        scroll = tk.Scrollbar(self)
        scroll.grid(row=0, column=1, sticky='ns')
        scroll.config(command=list_box.yview)
        list_box.config(yscrollcommand=scroll.set)
        list_box.bind('<<ListboxSelect>>', self.master.master.options_select)


class OptionsActions(tk.Frame):
    """The frame for the Twitch bot options list

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='options_action', *args, **kwargs)
        self._setup_app()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


class TwitchLogin(tk.Frame):
    """The Frame for the Twitch Login Options Section

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, logger: Logger, *args, **kwargs) -> None:
        super().__init__(name='twitch_login', *args, **kwargs)
        self.logger = logger
        # Variables for the form elements
        self.twitch_username = tk.StringVar()
        self.twitch_channel = tk.StringVar()
        self.oauth_token = tk.StringVar()
        # Load values from config
        self.config = self._load_config_values()
        # Setup grid
        self._setup_app()
        self._build_form()

    def _setup_app(self) -> None:
        """Setup the TK application and widgets
        """
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _build_form(self) -> None:
        """Build the form for the options page
        """
        self.heading_label = tk.Label(self, text='Twitch Login options',
                                      font=('Helvetica', 12, 'bold'))
        self.user_label = tk.Label(self, text='Twitch Username:')
        self.user_box = tk.Entry(self, name='twitch_username',
                                 textvariable=self.twitch_username)
        self.channel_label = tk.Label(self, text='Twitch channel:')
        self.channel_box = tk.Entry(self, name='twitch_channel',
                                    textvariable=self.twitch_channel)
        self.oauth_label = tk.Label(self, text='OAuth token:')
        self.oauth_val_label = tk.Label(self, textvariable=self.oauth_token)
        self.get_token_btn = tk.Button(self, text='Get new OAuth Token',
                                       command=self.get_oauth_token,
                                       name='get_oauth', state='normal')
        self.save_config_btn = tk.Button(self, text='Save Config',
                                         command=self._save_config_values,
                                         name='save_config', state='normal')
        # Grid Layout
        self.heading_label.grid(row=0, columnspan=2, sticky='ns', pady=5)
        self.user_label.grid(row=1, column=0, sticky='es', padx=5, pady=5)
        self.user_box.grid(row=1, column=1, sticky='ws', padx=5, pady=5)
        self.channel_label.grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.channel_box.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        self.oauth_label.grid(row=3, column=0, sticky='ne', padx=5, pady=5)
        self.oauth_val_label.grid(row=3, column=1, sticky='nw', padx=5, pady=5)
        self.get_token_btn.grid(row=4, column=1, sticky='nw', padx=5, pady=5)
        self.save_config_btn.grid(row=5, column=1, sticky='se', padx=5, pady=5)

    def get_oauth_token(self) -> None:
        """Start the Twitch OAuth Token process
        """
        # Disable button
        self.get_token_btn['state'] = 'disabled'
        # Update token
        get_twitch_oauth_token(self.oauth_token)

    def _load_config_values(self) -> ConfigParser:
        """Load the Twitch OAuth values from the config file
        """
        config = load_config(self.logger)
        self.twitch_username.set(config['twitch']['username'])
        self.twitch_channel.set(config['twitch']['channel'])
        self.oauth_token.set(config['twitch']['oauth_token'])
        return config

    def _save_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        self.config['twitch']['username'] = self.twitch_username.get()
        self.config['twitch']['channel'] = self.twitch_channel.get()
        self.config['twitch']['oauth_token'] = self.oauth_token.get()
        save_config(self.config, self.logger)


class TestOption(tk.Frame):
    """A holding Frame for further Options Sections

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(name='test_option', background='red', *args,
                         **kwargs)
