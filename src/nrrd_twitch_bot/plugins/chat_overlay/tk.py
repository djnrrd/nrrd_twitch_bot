"""An example tk config object for the OBS chat overlay plugin
"""
from logging import Logger
import tkinter as tk
from tkinter import ttk, font
from nrrd_twitch_bot import load_config, save_config


class PluginOptions(tk.Frame):
    """A holding Frame for further Options Sections

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, logger: Logger, *args, **kwargs) -> None:
        super().__init__(name='chat_overlay', *args, **kwargs)
        self.logger = logger
        self.chat_font = tk.StringVar()
        self.font_size = tk.StringVar()
        self._setup_app()
        self._build_form()

    def _setup_app(self) -> None:
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _build_form(self) -> None:
        header_label = tk.Label(self, text='Chat Overlay Options',
                                font=('Helvetica', 12, 'bold'))
        font_list = list(font.families())
        font_label = tk.Label(self, text='Overlay Font')
        font_chooser = ttk.Combobox(self, values=font_list,
                                    textvariable=self.chat_font)
        font_chooser.set('Arial')
        font_sizes = ['16px', '20px', '24px', '28px', '32px', '36px', '40px']
        size_label = tk.Label(self, text='Default font size')
        size_chooser = ttk.Combobox(self, values=font_sizes,
                                    textvariable=self.font_size)
        size_chooser.set('16px')
        save_config_btn = tk.Button(self, text='Save',
                                    command=self._save_config_values,
                                    name='save_config', state='normal')
        header_label.grid(row=0, columnspan=2, sticky='ns', pady=5)
        font_label.grid(row=1, column=0, sticky='es', pady=5, padx=5)
        font_chooser.grid(row=1, column=1, sticky='ws', pady=5, padx=5)
        size_label.grid(row=2, column=0, sticky='es', pady=5, padx=5)
        size_chooser.grid(row=2, column=1, sticky='ws', pady=5, padx=5)
        save_config_btn.grid(row=4, column=1, sticky='es', pady=5, padx=5)

    def _save_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        config = load_config('chat_overlay.ini')
        config['DEFAULT']['chat_font'] = self.chat_font.get()
        config['DEFAULT']['font_size'] = self.font_size.get()
        save_config(config, 'chat_overlay.ini')
