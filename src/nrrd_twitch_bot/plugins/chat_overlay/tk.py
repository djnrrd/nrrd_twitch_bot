"""An example tk config object for the OBS chat overlay plugin
"""
from logging import Logger
import tkinter as tk
from tkinter import ttk, font
from tkinter.colorchooser import askcolor
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
        self.font_colour = tk.StringVar()
        self.pronoun_option = tk.BooleanVar()
        self._setup_app()
        self._build_form()
        self._load_config_values()

    def _setup_app(self) -> None:
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(6, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _build_form(self) -> None:
        # Header
        header_label = tk.Label(self, text='Chat Overlay Options',
                                font=('Helvetica', 12, 'bold'))
        # Default Font
        font_list = list(font.families())
        font_label = tk.Label(self, text='Overlay Font')
        font_chooser = ttk.Combobox(self, values=font_list,
                                    textvariable=self.chat_font)
        # Default Font Size
        font_sizes = ['16px', '20px', '24px', '28px', '32px', '36px', '40px']
        size_label = tk.Label(self, text='Default font size')
        size_chooser = ttk.Combobox(self, values=font_sizes,
                                    textvariable=self.font_size)
        # Colour chooser
        colour_label = tk.Label(self, text='Default font colour')
        colour_box = tk.Entry(self, textvariable=self.font_colour)
        colour_picker = tk.Button(self, text='Select colour',
                                  command=self._font_colour_chooser,
                                  name='font_colour', state='normal')
        # Pronouns options
        pronouns_label = tk.Label(self, text='Display alejo.io pronouns')
        pronouns_option = tk.Checkbutton(self, variable=self.pronoun_option)
        # Save Button
        save_config_btn = tk.Button(self, text='Save',
                                    command=self._save_config_values,
                                    name='save_config', state='normal')
        # Grid layouts
        header_label.grid(row=0, columnspan=2, sticky='ns', pady=5)
        font_label.grid(row=1, column=0, sticky='es', pady=5, padx=5)
        font_chooser.grid(row=1, column=1, sticky='ws', pady=5, padx=5)
        size_label.grid(row=2, column=0, sticky='es', pady=5, padx=5)
        size_chooser.grid(row=2, column=1, sticky='ws', pady=5, padx=5)
        colour_label.grid(row=3, column=0, sticky='es', pady=5, padx=5)
        colour_box.grid(row=3, column=1, sticky='ws', pady=5, padx=5)
        colour_picker.grid(row=3, column=1, sticky='s', pady=5, padx=5)
        pronouns_label.grid(row=4, column=0, sticky='es', pady=5, padx=5)
        pronouns_option.grid(row=4, column=1, sticky='ws', pady=5, padx=5)
        save_config_btn.grid(row=6, column=1, sticky='es', pady=5, padx=5)

    def _save_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        config = load_config('chat_overlay.ini')
        config['DEFAULT']['chat_font'] = self.chat_font.get()
        config['DEFAULT']['font_size'] = self.font_size.get()
        config['DEFAULT']['font_colour'] = self.font_colour.get()
        config['DEFAULT']['pronoun_option'] = str(self.pronoun_option.get())
        save_config(config, 'chat_overlay.ini')

    def _load_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        config = load_config('chat_overlay.ini')
        self.chat_font.set(config['DEFAULT'].get('chat_font', 'Arial'))
        self.font_size.set(config['DEFAULT'].get('font_size', '16px'))
        self.font_colour.set(config['DEFAULT'].get('font_colour', 'white'))
        self.pronoun_option.set(eval(config['DEFAULT'].get('pronoun_option',
                                                           True)))

    def _font_colour_chooser(self) -> None:
        colour = askcolor(title='Default Font Colour')
        self.font_colour.set(colour[1])
