"""An example tk config object for the OBS chat overlay plugin
"""
from logging import Logger
import tkinter as tk
from tkinter import ttk, font, filedialog
from tkinter.colorchooser import askcolor
from nrrd_twitch_bot import load_config, save_config


class PluginOptions(ttk.Frame):
    """A holding Frame for further Options Sections

    :param kwargs: List of keyword arguments for a Tk Frame
    """

    def __init__(self, logger: Logger, *args, **kwargs) -> None:
        super().__init__(name='chat_overlay', *args, **kwargs)
        self.logger = logger
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.chat_style = tk.StringVar()
        self.chat_font = tk.StringVar()
        self.font_size = tk.StringVar()
        self.font_colour = tk.StringVar()
        self.badges_option = tk.BooleanVar()
        self.timeout_option = tk.IntVar()
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
        self._enable_css_options()

    def _setup_app(self) -> None:
        """Setup the grid
        """
        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(1, weight=0)
        self.scrollable_frame.grid_rowconfigure(2, weight=0)
        self.scrollable_frame.grid_rowconfigure(3, weight=0)
        self.scrollable_frame.grid_rowconfigure(4, weight=0)
        self.scrollable_frame.grid_rowconfigure(5, weight=0)
        self.scrollable_frame.grid_rowconfigure(6, weight=0)
        self.scrollable_frame.grid_rowconfigure(7, weight=0)
        self.scrollable_frame.grid_rowconfigure(8, weight=0)
        self.scrollable_frame.grid_rowconfigure(9, weight=0)
        self.scrollable_frame.grid_rowconfigure(10, weight=0)
        self.scrollable_frame.grid_rowconfigure(11, weight=0)
        self.scrollable_frame.grid_rowconfigure(12, weight=0)
        self.scrollable_frame.grid_rowconfigure(13, weight=0)
        self.scrollable_frame.grid_rowconfigure(14, weight=1)
        self.scrollable_frame.grid_columnconfigure(0, weight=0)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.grid_columnconfigure(2, weight=0)

    def _build_form(self) -> None:
        """Build all the form elements
        """
        # Header
        header_label = tk.Label(self.scrollable_frame,
                                text='Chat Overlay Options',
                                font=('Helvetica', 12, 'bold'))
        # Theme selection
        style_list = ['Default Nrrd', 'Twitch', '2 Columns', 'Boxes']
        style_label = tk.Label(self.scrollable_frame, text='Chat Theme',
                               wraplength=250)
        style_chooser = ttk.Combobox(self.scrollable_frame, values=style_list,
                                     textvariable=self.chat_style)
        # Default Font
        font_list = list(font.families())
        font_list.sort()
        font_label = tk.Label(self.scrollable_frame, text='Overlay Font',
                              wraplength=250)
        font_chooser = ttk.Combobox(self.scrollable_frame, values=font_list,
                                    textvariable=self.chat_font)
        # Default Font Size
        font_sizes = ['16px', '20px', '24px', '28px', '32px', '36px', '40px']
        size_label = tk.Label(self.scrollable_frame, text='Default font size',
                              wraplength=250)
        size_chooser = ttk.Combobox(self.scrollable_frame, values=font_sizes,
                                    textvariable=self.font_size)
        # Colour chooser
        colour_label = tk.Label(self.scrollable_frame,
                                text='Default font colour', wraplength=250)
        colour_box = tk.Entry(self.scrollable_frame,
                              textvariable=self.font_colour)
        colour_picker = tk.Button(self.scrollable_frame, text='Select colour',
                                  command=self._font_colour_chooser,
                                  name='font_colour', state='normal')
        # Badges options
        badges_label = tk.Label(self.scrollable_frame, text='Display badges',
                                wraplength=250)
        badges_option = tk.Checkbutton(self.scrollable_frame,
                                       variable=self.badges_option)
        # Chat timeout options
        timeout_label = tk.Label(self.scrollable_frame,
                                 text='Hide messages after: (Seconds. Leave '
                                      'as 0 to disable)', wraplength=250)
        timeout_option = tk.Entry(self.scrollable_frame,
                                  textvariable=self.timeout_option)
        # BTTV Options
        bttv_label = tk.Label(self.scrollable_frame, text='Display BTTV emotes',
                              wraplength=250)
        bttv_option = tk.Checkbutton(self.scrollable_frame,
                                     variable=self.bttv_option)
        # Pronouns options
        pronoun_label = tk.Label(self.scrollable_frame,
                                 text='Display alejo.io pronouns',
                                 wraplength=250)
        pronoun_option = tk.Checkbutton(self.scrollable_frame,
                                        variable=self.pronoun_option,
                                        command=self._enable_pronoun_options)
        # Pronouns font
        pronoun_font_label = tk.Label(self.scrollable_frame,
                                      text='Pronoun font',
                                      name='pronoun_font_lbl', wraplength=250)
        pronoun_font = ttk.Combobox(self.scrollable_frame, values=font_list,
                                    name='pronoun_font',
                                    textvariable=self.pronoun_font)
        # pronouns colour
        pronoun_colour_label = tk.Label(self.scrollable_frame,
                                        text='Pronoun colour',
                                        name='pronoun_colour_lbl',
                                        wraplength=250)
        pronoun_colour = tk.Entry(self.scrollable_frame,
                                  textvariable=self.pronoun_colour,
                                  name='pronoun_colour')
        pronoun_colour_picker = tk.Button(self.scrollable_frame,
                                          text='Select colour',
                                          command=self._pronoun_colour_chooser,
                                          name='pronoun_colour_picker',
                                          state='normal')
        # Custom CSS option
        custom_css_label = tk.Label(self.scrollable_frame,
                                    text='Use custom CSS file (ignores style '
                                         'settings above)', wraplength=250)
        custom_css_option = tk.Checkbutton(self.scrollable_frame,
                                           variable=self.custom_css,
                                           command=self._enable_css_options)
        # Custom CSS File chooser
        css_file_label = tk.Label(self.scrollable_frame,
                                  text='Select custom CSS file',
                                  name='css_file_lbl', wraplength=250)
        css_file_picker = tk.Button(self.scrollable_frame,
                                    text='Select File...',
                                    command=self._css_file_chooser,
                                    name='css_file_btn', state='normal')
        css_chosen_file_label = tk.Label(self.scrollable_frame,
                                         textvariable=self.custom_css_path,
                                         name='css_chosen_file_lbl',
                                         wraplength=250)
        # Save Button
        save_config_btn = tk.Button(self.scrollable_frame, text='Save',
                                    command=self._save_config_values,
                                    name='save_config', state='normal')
        # Grid layouts
        header_label.grid(row=0, columnspan=3, sticky='new', pady=5)
        style_label.grid(row=1, column=0, sticky='se', pady=5, padx=5)
        style_chooser.grid(row=1, column=1, columnspan=2, sticky='sw', pady=5,
                           padx=5)
        font_label.grid(row=2, column=0, sticky='se', pady=5, padx=5)
        font_chooser.grid(row=2, column=1, columnspan=2, sticky='sw', pady=5,
                          padx=5)
        size_label.grid(row=3, column=0, sticky='e', pady=5, padx=5)
        size_chooser.grid(row=3, column=1, columnspan=2, sticky='w', pady=5,
                          padx=5)
        colour_label.grid(row=4, column=0, sticky='e', pady=5, padx=5)
        colour_box.grid(row=4, column=1, sticky='w', pady=5, padx=5)
        colour_picker.grid(row=4, column=2, sticky='w', pady=5, padx=5)
        badges_label.grid(row=5, column=0, sticky='e', pady=5, padx=5)
        badges_option.grid(row=5, column=1, columnspan=2, sticky='w', pady=5,
                           padx=5)
        timeout_label.grid(row=6, column=0, sticky='e', pady=5, padx=5)
        timeout_option.grid(row=6, column=1, columnspan=2, sticky='w', pady=5,
                            padx=5)
        bttv_label.grid(row=7, column=0, sticky='e', pady=5, padx=5)
        bttv_option.grid(row=7, column=1, columnspan=2, sticky='w', pady=5,
                         padx=5)
        pronoun_label.grid(row=8, column=0, sticky='e', pady=5, padx=5)
        pronoun_option.grid(row=8, column=1, columnspan=2, sticky='w', pady=5,
                            padx=5)
        pronoun_font_label.grid(row=9, column=0, sticky='e', pady=5, padx=5)
        pronoun_font.grid(row=9, column=1, sticky='w', pady=5, padx=5)
        pronoun_colour_label.grid(row=10, column=0, sticky='e', pady=5, padx=5)
        pronoun_colour.grid(row=10, column=1, sticky='w',pady=5, padx=5)
        pronoun_colour_picker.grid(row=10, column=2, sticky='w', pady=5, padx=5)
        custom_css_label.grid(row=11, column=0, sticky='e', pady=5, padx=5)
        custom_css_option.grid(row=11, column=1, columnspan=2, sticky='w',
                               pady=5, padx=5)
        css_file_label.grid(row=12, column=0, sticky='e', pady=5, padx=5)
        css_file_picker.grid(row=12, column=1, columnspan=2, sticky='w',
                             pady=5, padx=5)
        css_chosen_file_label.grid(row=13, column=1, columnspan=2,
                                   sticky='w', pady=5, padx=5)
        save_config_btn.grid(row=14, column=2, sticky='es', pady=5, padx=5)

    def _save_config_values(self) -> None:
        """Save the Twitch OAuth values to the config file
        """
        config = load_config('chat_overlay.ini')
        config['DEFAULT']['chat_font'] = self.chat_font.get()
        config['DEFAULT']['font_size'] = self.font_size.get()
        config['DEFAULT']['font_colour'] = self.font_colour.get()
        config['DEFAULT']['badges_option'] = str(self.badges_option.get())
        config['DEFAULT']['timeout_message'] = str(self.timeout_option.get())
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
        self.timeout_option.set(int(config['DEFAULT'].get('timeout_message',
                                                          '0')))
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
        pronoun_widgets = [(x, y) for x, y in
                           self.scrollable_frame.children.items()
                           if 'pronoun' in x]
        if self.pronoun_option.get():
            for widget in pronoun_widgets:
                widget[1].config(state='normal')
        else:
            for widget in pronoun_widgets:
                widget[1].config(state='disabled')

    def _enable_css_options(self) -> None:
        """Enable widgets related to the customer CSS options"""
        css_widgets = [(x, y) for x, y in self.scrollable_frame.children.items()
                       if 'css' in x]
        if self.custom_css.get():
            for widget in css_widgets:
                widget[1].config(state='normal')
        else:
            for widget in css_widgets:
                widget[1].config(state='disabled')
