"""An example tk config object for the OBS chat overlay plugin
"""
from logging import Logger
import tkinter as tk
from tkinter import ttk, font, filedialog
from tkinter.colorchooser import askcolor
from nrrd_twitch_bot import load_config, save_config


class PluginOptions(tk.Frame):
    """A holding Frame for further Options Sections

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, logger: Logger, *args, **kwargs) -> None:
        super().__init__(name='chat_overlay', *args, **kwargs)
        self.logger = logger
        self.chat_style = tk.StringVar()
        self.chat_font = tk.StringVar()
        self.font_size = tk.StringVar()
        self.font_colour = tk.StringVar()
        self.badges_option = tk.BooleanVar()
        self.bttv_option = tk.BooleanVar()
        self.pronoun_option = tk.BooleanVar()
        self.pronoun_font = tk.StringVar()
        self.pronoun_colour = tk.StringVar()
        self.custom_css = tk.BooleanVar()
        self.custom_css_path = tk.StringVar()
        self._setup_app()
        self._build_form()
        self._load_config_values()
        self._enable_pronoun_options()

    def _setup_app(self) -> None:
        """Setup te grid
        """
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=0)
        self.grid_rowconfigure(7, weight=0)
        self.grid_rowconfigure(8, weight=0)
        self.grid_rowconfigure(9, weight=0)
        self.grid_rowconfigure(10, weight=0)
        self.grid_rowconfigure(11, weight=0)
        self.grid_rowconfigure(12, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _build_form(self) -> None:
        """Build all the form elements
        """
        # Header
        header_label = tk.Label(self, text='Chat Overlay Options',
                                font=('Helvetica', 12, 'bold'))
        # Theme selection
        style_list = ['Default Nrrd', 'Twitch', '2 Columns', 'Boxes']
        style_label = tk.Label(self, text='Chat Theme')
        style_chooser = ttk.Combobox(self, values=style_list,
                                     textvariable=self.chat_style)
        # Default Font
        font_list = list(font.families())
        font_list.sort()
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
        # Badges options
        badges_label = tk.Label(self, text='Display badges')
        badges_option = tk.Checkbutton(self, variable=self.badges_option)
        # BTTV Options
        bttv_label = tk.Label(self, text='Display BTTV emotes')
        bttv_option = tk.Checkbutton(self, variable=self.bttv_option)
        # Pronouns options
        pronoun_label = tk.Label(self, text='Display alejo.io pronouns')
        pronoun_option = tk.Checkbutton(self, variable=self.pronoun_option,
                                        command=self._enable_pronoun_options)
        # Pronouns font
        pronoun_font_label = tk.Label(self, text='Pronoun font',
                                      name='pronoun_font_lbl')
        pronoun_font = ttk.Combobox(self, values=font_list, name='pronoun_font',
                                    textvariable=self.pronoun_font)
        # pronouns colour
        pronoun_colour_label = tk.Label(self, text='Pronoun colour',
                                        name='pronoun_colour_lbl')
        pronoun_colour = tk.Entry(self, textvariable=self.pronoun_colour,
                                  name='pronoun_colour')
        pronoun_colour_picker = tk.Button(self, text='Select colour',
                                          command=self._pronoun_colour_chooser,
                                          name='pronoun_colour_picker',
                                          state='normal')
        # Custom CSS option
        custom_css_label = tk.Label(self, text='Use custom CSS file (ignores '
                                               'style settings above)')
        custom_css_option = tk.Checkbutton(self, variable=self.custom_css,
                                           command=self._enable_css_options)
        # Custom CSS File chooser
        css_file_label = tk.Label(self, text='Select custom CSS file',
                                  name='css_file_lbl')
        css_file_picker = tk.Button(self, text='Select File...',
                                    command=self._css_file_chooser,
                                    name='css_file_btn', state='normal')


        # Save Button
        save_config_btn = tk.Button(self, text='Save',
                                    command=self._save_config_values,
                                    name='save_config', state='normal')
        # Grid layouts
        header_label.grid(row=0, columnspan=2, sticky='new', pady=5)
        style_label.grid(row=1, column=0, sticky='se', pady=5, padx=5)
        style_chooser.grid(row=1, column=1, sticky='sw', pady=5, padx=5)
        font_label.grid(row=2, column=0, sticky='se', pady=5, padx=5)
        font_chooser.grid(row=2, column=1, sticky='sw', pady=5, padx=5)
        size_label.grid(row=3, column=0, sticky='e', pady=5, padx=5)
        size_chooser.grid(row=3, column=1, sticky='w', pady=5, padx=5)
        colour_label.grid(row=4, column=0, sticky='e', pady=5, padx=5)
        colour_box.grid(row=4, column=1, sticky='w', pady=5, padx=5)
        colour_picker.grid(row=4, column=1, pady=5, padx=5)
        badges_label.grid(row=5, column=0, sticky='e', pady=5, padx=5)
        badges_option.grid(row=5, column=1, sticky='w', pady=5, padx=5)
        bttv_label.grid(row=6, column=0, sticky='e', pady=5, padx=5)
        bttv_option.grid(row=6, column=1, sticky='w', pady=5, padx=5)
        pronoun_label.grid(row=7, column=0, sticky='e', pady=5, padx=5)
        pronoun_option.grid(row=7, column=1, sticky='w', pady=5, padx=5)
        pronoun_font_label.grid(row=8, column=0, sticky='e', pady=5, padx=5)
        pronoun_font.grid(row=8, column=1, sticky='w', pady=5, padx=5)
        pronoun_colour_label.grid(row=9, column=0, sticky='e', pady=5, padx=5)
        pronoun_colour.grid(row=9, column=1, sticky='w', pady=5, padx=5)
        pronoun_colour_picker.grid(row=9, column=1, pady=5, padx=5)
        custom_css_label.grid(row=10, column=0, sticky='e', pady=5, padx=5)
        custom_css_option.grid(row=10, column=1, sticky='w', pady=5, padx=5)
        css_file_label.grid(row=11, column=0, sticky='e', pady=5, padx=5)
        css_file_picker.grid(row=11, column=1, sticky='w', pady=5, padx=5)
        save_config_btn.grid(row=12, column=1, sticky='es', pady=5, padx=5)

    def _save_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        config = load_config('chat_overlay.ini')
        config['DEFAULT']['chat_font'] = self.chat_font.get()
        config['DEFAULT']['font_size'] = self.font_size.get()
        config['DEFAULT']['font_colour'] = self.font_colour.get()
        config['DEFAULT']['badges_option'] = str(self.badges_option.get())
        config['DEFAULT']['bttv_option'] = str(self.bttv_option.get())
        config['DEFAULT']['pronoun_option'] = str(self.pronoun_option.get())
        config['DEFAULT']['pronoun_font'] = self.pronoun_font.get()
        config['DEFAULT']['pronoun_colour'] = self.pronoun_colour.get()
        config['DEFAULT']['chat_style'] = self.chat_style.get()
        config['DEFAULT']['custom_css'] = str(self.custom_css.get())
        config['DEFAULT']['custom_css_path'] = self.custom_css_path.get()
        save_config(config, 'chat_overlay.ini')

    def _load_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        config = load_config('chat_overlay.ini')
        self.chat_font.set(config['DEFAULT'].get('chat_font', 'Arial'))
        self.font_size.set(config['DEFAULT'].get('font_size', '16px'))
        self.font_colour.set(config['DEFAULT'].get('font_colour', 'white'))
        self.badges_option.set(eval(config['DEFAULT'].get('badges_option',
                                                          'True')))
        self.bttv_option.set(eval(config['DEFAULT'].get('bttv_option', 'True')))
        self.pronoun_option.set(eval(config['DEFAULT'].get('pronoun_option',
                                                           'True')))
        self.pronoun_font.set(config['DEFAULT'].get('pronoun_font',
                                                    'Courier New'))
        self.pronoun_colour.set(config['DEFAULT'].get('pronoun_colour',
                                                      'lightgray'))
        self.chat_style.set(config['DEFAULT'].get('chat_style', 'Default Nrrd'))
        self.custom_css.set(eval(config['DEFAULT'].get('custom_css', 'False')))
        self.custom_css_path.set(config['DEFAULT'].get('custom_css_path', ''))

    def _font_colour_chooser(self) -> None:
        """Launch a colour picker for the main Font"""
        colour = askcolor(title='Default Font Colour')
        self.font_colour.set(colour[1])

    def _pronoun_colour_chooser(self) -> None:
        """Launch a colour picker for the pronoun Font"""
        colour = askcolor(title='Pronoun Font Colour')
        self.pronoun_colour.set(colour[1])

    def _css_file_chooser(self) -> None:
        """Launch a file picker for custom CSS"""
        filetypes = (('CSS files', '*.css'), ('All files', '*.*'))
        self.custom_css_path.set(
            filedialog.askopenfilename(title='Select CSS File',
                                       filetypes=filetypes)
        )

    def _enable_pronoun_options(self) -> None:
        """Enable widgets related to the Pronoun options"""
        pronoun_widgets = [x for x in self.children if 'pronoun' in x]
        if self.pronoun_option.get():
            for widget_name in pronoun_widgets:
                self.nametowidget(widget_name).config(state='normal')
        else:
            for widget_name in pronoun_widgets:
                self.nametowidget(widget_name).config(state='disabled')

    def _enable_css_options(self) -> None:
        """Enable widgets related to the customer CSS options"""
        css_widgets = [x for x in self.children if 'css' in x]
        if self.custom_css.get():
            for widget_name in css_widgets:
                self.nametowidget(widget_name).config(state='normal')
        else:
            for widget_name in css_widgets:
                self.nametowidget(widget_name).config(state='disabled')
