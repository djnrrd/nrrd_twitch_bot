"""An example tk config object for the OBS chat overlay plugin
"""
from logging import Logger
import tkinter as tk
from tkinter import ttk, font


class PluginOptions(tk.Frame):
    """A holding Frame for further Options Sections

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, logger: Logger, *args, **kwargs) -> None:
        super().__init__(name='chat_overlay', *args, **kwargs)
        self.logger = logger
        self.chat_font = tk.StringVar()
        self._setup_app()
        self._build_form()

    def _setup_app(self) -> None:
        self.grid_rowconfigure(0, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _build_form(self) -> None:
        font_list = list(font.families())
        font_label = tk.Label(self, text='Overlay Font',
                              font=('Helvetica', 12, 'bold'))
        font_chooser = ttk.Combobox(self, values=font_list,
                                    textvariable=self.chat_font)
        font_chooser.set('Arial')
        font_label.grid(row=0, column=0, sticky='ns', pady=5)
        font_chooser.grid(row=0, column=1, sticky='ns', pady=5)
