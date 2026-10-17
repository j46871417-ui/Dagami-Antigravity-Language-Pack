"""Native Tk view using Dagami Agent Proxy Fluent tokens and spacing."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk

UI_FONT = 'Segoe UI'
MONO_FONT = 'Consolas'

COLORS = dict(background='#f3f5f8', surface='#ffffff', text='#1d232c',
              muted='#4e5b6b', border='#cfd7e2', accent='#005fb8',
              sidebar='#ebf0f6', selected='#e2edf9', hover='#ebf0f7')


class Card(tk.Canvas):
    """Rounded surface only; all input controls stay native Tk/ttk widgets."""
    def __init__(self, parent, padding=12, **kwargs):
        super().__init__(parent, background=COLORS['background'], highlightthickness=0,
                         borderwidth=0, takefocus=False, **kwargs)
        self.padding = padding
        self.body = ttk.Frame(self, style='Card.TFrame')
        self.window = self.create_window(padding, padding, window=self.body, anchor='nw')
        self.bind('<Configure>', self._layout)
        self.body.bind('<Configure>', self._requested)

    def _requested(self, _=None):
        self.configure(height=self.body.winfo_reqheight() + self.padding * 2)

    def _layout(self, event):
        w, h, r = event.width - 1, event.height - 1, 8
        self.delete('surface')
        points = [r, 0, w-r, 0, w, 0, w, r, w, h-r, w, h, w-r, h,
                  r, h, 0, h, 0, h-r, 0, r, 0, 0]
        self.create_polygon(points, smooth=True, splinesteps=24, fill=COLORS['surface'],
                            outline=COLORS['border'], tags='surface')
        self.tag_lower('surface')
        self.itemconfigure(self.window, width=max(1, event.width - self.padding * 2), height=max(1, event.height - self.padding * 2))


def enable_dpi_awareness():
    import sys
    if sys.platform != 'win32':
        return
    import ctypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    try:
        function = user32.SetProcessDpiAwarenessContext
        function.argtypes = [ctypes.c_void_p]
        function.restype = ctypes.c_int
        if function(ctypes.c_void_p(-4)):
            return
    except AttributeError:
        pass
    try:
        user32.SetProcessDPIAware()
    except AttributeError:
        pass


def configure_checkboxes(root, style):
    """Replace only the indicator; ttk keeps input, focus and variable handling."""
    import math
    scale = max(1.0, root.winfo_fpixels('1i') / 96)
    size = round(18 * scale)
    images = []
    def rgb(color):
        return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    def icon(fill, border, checked=False, tick='#ffffff'):
        image = tk.PhotoImage(master=root, width=size + round(8*scale), height=size)
        colors = [rgb(color) for color in ('#ffffff', border, fill, tick)]
        def rounded(x, y, inset, radius):
            lo, hi = inset + radius, 18 - inset - radius
            dx, dy = max(lo-x, 0, x-hi), max(lo-y, 0, y-hi)
            return dx*dx + dy*dy <= radius*radius
        def distance(x, y, a, b):
            dx, dy = b[0]-a[0], b[1]-a[1]
            t = max(0, min(1, ((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
            return math.hypot(x-a[0]-t*dx, y-a[1]-t*dy)
        rows = []
        for py in range(size):
            row = []
            for px in range(size + round(8*scale)):
                sums = [0, 0, 0]
                for ox, oy in ((.25,.25),(.75,.25),(.25,.75),(.75,.75)):
                    x, y = (px+ox)/scale, (py+oy)/scale
                    index = 0
                    if rounded(x,y,1,3):
                        index = 2 if rounded(x,y,2.2,2) else 1
                        if checked and min(distance(x,y,(4.5,9),(7.5,12)), distance(x,y,(7.5,12),(13.5,5.8))) <= 1:
                            index = 3
                    for channel in range(3): sums[channel] += colors[index][channel]
                row.append('#%02x%02x%02x' % tuple(round(value/4) for value in sums))
            rows.append('{'+' '.join(row)+'}')
        image.put(' '.join(rows))
        images.append(image)
        return image
    normal = icon('#ffffff', '#6b7889')
    hover = icon('#eaf3ff', '#005fb8')
    pressed = icon('#d5e6fa', '#004282')
    selected = icon('#005fb8', '#005fb8', True)
    selected_hover = icon('#004e9a', '#004282', True)
    selected_pressed = icon('#00376e', '#00376e', True)
    disabled = icon('#f0f2f5', '#b8c0cc')
    disabled_selected = icon('#aab5c4', '#aab5c4', True)
    name = 'Dagami.Check.indicator'
    if name not in style.element_names():
        style.element_create(name, 'image', normal,
            ('disabled', 'selected', disabled_selected), ('disabled', disabled),
            ('pressed', 'selected', selected_pressed), ('pressed', pressed),
            ('active', 'selected', selected_hover), ('active', hover), ('selected', selected), sticky='w')
    def replace_indicator(layout):
        result = []
        for name_, options in layout:
            options = dict(options)
            if 'children' in options:
                options['children'] = replace_indicator(options['children'])
            result.append((name if name_.endswith('.indicator') else name_, options))
        return result
    style.layout('Card.TCheckbutton', replace_indicator(style.layout('TCheckbutton')))
    style.configure('Card.TCheckbutton', background='white', font=(UI_FONT, 10),
                    padding=(0, 3), focuscolor='#005fb8', focusthickness=2)
    style.map('Card.TCheckbutton', background=[('active', 'white')],
              foreground=[('disabled', '#7b8594'), ('active', '#004282')])
    root.option_add('*TCheckbutton.cursor', 'hand2')
    root._dagami_checkbox_images = images


def configure_theme(root):
    global UI_FONT, MONO_FONT
    import sys
    import tkinter.font as tkfont
    available = {name.lower(): name for name in tkfont.families(root)}
    choices = ['Segoe UI'] if sys.platform == 'win32' else (['SF Pro Text', 'Helvetica Neue', 'Helvetica'] if sys.platform == 'darwin' else ['Noto Sans', 'DejaVu Sans', 'Liberation Sans'])
    UI_FONT = next((available[name.lower()] for name in choices if name.lower() in available), tkfont.nametofont('TkDefaultFont',root=root).actual('family'))
    mono = ['Consolas', 'Menlo', 'DejaVu Sans Mono', 'Liberation Mono']
    MONO_FONT = next((available[name.lower()] for name in mono if name.lower() in available), tkfont.nametofont('TkFixedFont',root=root).actual('family'))
    style = ttk.Style(root)
    style.theme_use('clam')
    root.configure(background=COLORS['background'])
    root.option_add('*Font', (UI_FONT, 10))
    root.option_add('*Dialog.msg.font', (UI_FONT, 10))
    style.configure('.', font=(UI_FONT, 10), foreground=COLORS['text'],
                    background=COLORS['background'])
    for name, color in [('App', 'background'), ('Card', 'surface'), ('Sidebar', 'sidebar')]:
        style.configure(name+'.TFrame', background=COLORS[color])
        style.configure(name+'.TLabel', background=COLORS[color], foreground=COLORS['text'])
    style.configure('Muted.TLabel', background=COLORS['surface'], foreground=COLORS['muted'], font=(UI_FONT, 9))
    style.configure('Heading.TLabel', background=COLORS['background'], font=(UI_FONT, 18, 'bold'))
    style.configure('Title.TLabel', background=COLORS['surface'], font=(UI_FONT, 11, 'bold'))
    # Native active/pressed/focus states; no animation or layout change.
    root.option_add('*TButton.cursor', 'hand2')
    style.configure('TButton', background='#f8fafc', foreground=COLORS['text'],
                    bordercolor='#8190a2', lightcolor='#f8fafc', darkcolor='#f8fafc',
                    padding=(12, 6), borderwidth=1, relief='solid',
                    focuscolor=COLORS['accent'], focusthickness=2)
    style.map('TButton',
              background=[('disabled', '#eef0f3'), ('pressed', '#c2ddf7'), ('active', '#dcecff')],
              foreground=[('disabled', COLORS['muted']), ('pressed', '#00345f'), ('active', '#003e73')],
              bordercolor=[('disabled', '#cfd7e2'), ('pressed', '#004282'), ('active', COLORS['accent']), ('focus', COLORS['accent'])],
              lightcolor=[('disabled', '#eef0f3'), ('pressed', '#c2ddf7'), ('active', '#dcecff')],
              darkcolor=[('disabled', '#eef0f3'), ('pressed', '#c2ddf7'), ('active', '#dcecff')])
    style.configure('Primary.TButton', background=COLORS['accent'], foreground='white',
                    bordercolor=COLORS['accent'], lightcolor=COLORS['accent'], darkcolor=COLORS['accent'],
                    font=(UI_FONT, 10, 'bold'))
    style.map('Primary.TButton',
              background=[('disabled', '#e0e5ec'), ('pressed', '#00376e'), ('active', '#004b93')],
              foreground=[('disabled', '#5b6574'), ('!disabled', 'white')],
              bordercolor=[('disabled', '#cfd7e2'), ('pressed', '#002b56'), ('active', '#00376e'), ('focus', '#002f5c')],
              lightcolor=[('disabled', '#e0e5ec'), ('pressed', '#00376e'), ('active', '#004b93')],
              darkcolor=[('disabled', '#e0e5ec'), ('pressed', '#00376e'), ('active', '#004b93')])
    style.configure('Nav.TButton', background=COLORS['selected'], foreground=COLORS['accent'],
                    bordercolor='#6f9dce', lightcolor=COLORS['selected'], darkcolor=COLORS['selected'], anchor='w')
    style.configure('Link.TButton', background='#f8fafc', bordercolor='#8190a2',
                    lightcolor='#f8fafc', darkcolor='#f8fafc', borderwidth=1,
                    anchor='w', padding=(7, 5))
    style.configure('TEntry', fieldbackground='white', foreground=COLORS['text'], padding=6,
                    bordercolor='#8190a2', lightcolor='white', darkcolor='white')
    style.map('TEntry', bordercolor=[('focus', COLORS['accent'])])
    configure_checkboxes(root, style)
    style.configure('Language.TRadiobutton', background='#f7f9fc', foreground=COLORS['text'],
                    font=(UI_FONT, 10), padding=(10, 6), borderwidth=1,
                    relief='solid', focuscolor=COLORS['accent'], focusthickness=2)
    style.map('Language.TRadiobutton',
              background=[('disabled', '#eef0f3'), ('pressed', '#c2ddf7'), ('selected', 'active', '#c7def7'),
                          ('active', '#dcecff'), ('selected', COLORS['selected'])],
              foreground=[('disabled', COLORS['muted']), ('selected', COLORS['accent']), ('active', '#003e73')],
              bordercolor=[('disabled', '#cfd7e2'), ('focus', COLORS['accent']), ('active', COLORS['accent']),
                           ('selected', COLORS['accent']), ('!selected', '#8190a2')])
    style.configure('TProgressbar', background=COLORS['accent'], troughcolor=COLORS['border'], borderwidth=0)
    return style


def build_interface(owner):
    tk_, ttk_ = owner.tk, owner.ttk
    root = owner.root
    configure_theme(root)
    dpi = max(1.0, root.winfo_fpixels('1i') / 96)
    width = min(round(900*dpi), max(640, root.winfo_screenwidth() - 48))
    height = min(round(650*dpi), max(420, root.winfo_screenheight() - 96))
    root.geometry(f'{width}x{height}')
    root.minsize(min(round(840*dpi), width), min(round(600*dpi), height))
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    owner._input_controls = []
    owner._language_controls = []
    owner.operation_status = tk.StringVar(value='Перед запуском сохраните работу и закройте Antigravity.')

    side = ttk.Frame(root, style='Sidebar.TFrame', padding=(12, 16, 12, 12), width=round(156*dpi))
    side.grid(row=0, column=0, sticky='nsew')
    side.grid_propagate(False)
    side.columnconfigure(0, weight=1)
    side.rowconfigure(4, weight=1)
    brand = ttk.Frame(side, style='Sidebar.TFrame')
    brand.grid(row=0, column=0, sticky='ew', pady=(0, 18))
    try:
        owner._brand_image = tk.PhotoImage(file=str(owner.bundle_dir / 'assets' / 'app-icon-64.png'))
        scale = max(1, owner._brand_image.width() // 32)
        owner._brand_image = owner._brand_image.subsample(scale, scale)
        ttk.Label(brand, image=owner._brand_image, style='Sidebar.TLabel').grid(row=0, column=0, rowspan=2, padx=(0, 8))
        owner._window_icon = tk.PhotoImage(file=str(owner.bundle_dir / 'assets' / 'app-icon-256.png'))
        root.iconphoto(True, owner._window_icon)
    except tk.TclError:
        pass
    ttk.Label(brand, text='DAGAMI', font=(UI_FONT, 12, 'bold'), style='Sidebar.TLabel').grid(row=0, column=1, sticky='w')
    ttk.Label(brand, text='Language Pack', font=(UI_FONT, 9), foreground=COLORS['muted'], style='Sidebar.TLabel').grid(row=1, column=1, sticky='w')
    ttk.Button(side, text='Язык', style='Nav.TButton', command=lambda: owner._language_controls[0].focus_set()).grid(row=1, column=0, sticky='ew', pady=(0, 8))
    ttk.Button(side, text='Журнал', style='Link.TButton', command=lambda: owner.log_text.focus_set()).grid(row=2, column=0, sticky='ew')
    ttk.Label(side, text='Antigravity\nDesktop и IDE', style='Sidebar.TLabel', foreground=COLORS['muted'], font=(UI_FONT, 9)).grid(row=3, column=0, sticky='nw', pady=(20, 0))
    footer = ttk.Frame(side, style='Sidebar.TFrame')
    footer.grid(row=5, column=0, sticky='sew')
    ttk.Label(footer, text='Версия '+owner.version, foreground=COLORS['muted'], font=(UI_FONT, 9), style='Sidebar.TLabel').pack(anchor='w', pady=(0, 10))
    from update_ui import UpdatePanel
    owner.updates = UpdatePanel(owner, footer)
    owner.updates.button.pack_forget()
    owner.updates.button.configure(style='Link.TButton')
    owner.updates.button.pack(fill='x', pady=(0, 6))
    ttk.Button(footer, text='Чат сообщества', style='Link.TButton', command=owner._open_telegram).pack(fill='x', pady=(0, 6))
    ttk.Button(footer, text='Поддержать', style='Link.TButton', command=owner._open_donation).pack(fill='x')

    # The page uses normal grid layout. Only the journal scrolls.
    main = ttk.Frame(root, style='App.TFrame', padding=(16, 14, 16, 10))
    main.grid(row=0, column=1, sticky='nsew')
    main.columnconfigure(0, weight=1)
    main.rowconfigure(6, weight=1)
    ttk.Label(main, text='Язык приложения', style='Heading.TLabel').grid(row=1, column=0, sticky='w')
    ttk.Label(main, text='Языковой пакет для Antigravity Desktop и IDE.', style='App.TLabel', foreground=COLORS['muted']).grid(row=2, column=0, sticky='w', pady=(2, 10))

    language = Card(main)
    language.grid(row=3, column=0, sticky='ew', pady=(0, 10))
    language.body.columnconfigure(0, weight=1)
    heading = ttk.Frame(language.body, style='Card.TFrame')
    heading.grid(row=0, column=0, sticky='ew')
    ttk.Label(heading, text='1. Выберите язык', style='Title.TLabel').pack(side='left')
    ttk.Label(heading, text='Обязательный выбор', style='Muted.TLabel').pack(side='right')
    languages = ttk.Frame(language.body, style='Card.TFrame')
    languages.grid(row=1, column=0, sticky='ew', pady=(8, 4))
    for column in range(3): languages.columnconfigure(column, weight=1, uniform='languages')
    for index, (label, code) in enumerate(owner.lang_choices.items()):
        radio = ttk.Radiobutton(languages, text=label, value=label, variable=owner.selected_lang_var,
                                style='Language.TRadiobutton', takefocus=True)
        radio.grid(row=index//3, column=index%3, sticky='ew', padx=(0 if index%3 == 0 else 5, 0 if index%3 == 2 else 5), pady=(0, 4))
        owner._language_controls.append(radio)
    owner.language_hint = ttk.Label(language.body, style='Muted.TLabel')
    owner.language_hint.grid(row=2, column=0, sticky='w')

    apps = Card(main, padding=12)
    apps.grid(row=4, column=0, sticky='ew', pady=(0, 10))
    apps.body.columnconfigure(0, weight=1)
    ttk.Label(apps.body, text='2. Выберите приложения', style='Title.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 10))
    for index, (title, var, path, browse, status_attr) in enumerate([
        ('Antigravity IDE', owner.opt_ide, owner.ide_path_var, owner._browse_ide, 'ide_status_label'),
        ('Antigravity Desktop', owner.opt_desktop, owner.desktop_path_var, owner._browse_desktop, 'desk_status_label')]):
        row = ttk.Frame(apps.body, style='Card.TFrame')
        row.grid(row=index*2+1, column=0, sticky='ew', pady=(0, 5))
        check = ttk.Checkbutton(row, text=title, variable=var, style='Card.TCheckbutton', takefocus=True)
        check.pack(side='left')
        status = ttk.Label(row, style='Muted.TLabel')
        status.pack(side='right')
        setattr(owner, status_attr, status)
        fields = ttk.Frame(apps.body, style='Card.TFrame')
        fields.grid(row=index*2+2, column=0, sticky='ew', pady=(0, 7 if index == 0 else 0))
        fields.columnconfigure(0, weight=1)
        entry = ttk.Entry(fields, textvariable=path)
        entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        button = ttk.Button(fields, text='Выбрать папку', command=browse)
        button.grid(row=0, column=1)
        owner._input_controls.extend([check, entry, button])
        entry.bind('<FocusOut>', lambda _: owner._update_status())

    actions = ttk.Frame(main, style='App.TFrame')
    actions.grid(row=5, column=0, sticky='ew', pady=(0, 10))
    owner.btn_install = ttk.Button(actions, text='Установить: Русский', style='Primary.TButton', command=owner._on_install)
    owner.btn_install.pack(side='left', padx=(0, 10))
    owner.btn_restore = ttk.Button(actions, text='Вернуть English', command=owner._on_restore)
    owner.btn_restore.pack(side='left')

    journal = Card(main, padding=10)
    journal.grid(row=6, column=0, sticky='nsew')
    journal.body.rowconfigure(1, weight=1)
    journal.body.columnconfigure(0, weight=1)
    ttk.Label(journal.body, text='Журнал', style='Title.TLabel').grid(row=0, column=0, sticky='w', pady=(0, 8))
    owner.log_text = tk.Text(journal.body, wrap='word', font=(MONO_FONT, 9), height=3,
                             background='white', foreground=COLORS['muted'], borderwidth=0,
                             highlightthickness=1, highlightbackground=COLORS['border'],
                             highlightcolor=COLORS['accent'], padx=8, pady=5, takefocus=True)
    owner.log_text.grid(row=1, column=0, sticky='nsew')
    scrollbar = ttk.Scrollbar(journal.body, command=owner.log_text.yview)
    scrollbar.grid(row=1, column=1, sticky='ns')
    owner.log_text.configure(yscrollcommand=scrollbar.set)
    owner.progress = ttk.Progressbar(main, mode='indeterminate', length=140)
    owner.progress.grid(row=7, column=0, sticky='ew', pady=(6, 4))
    owner.progress.grid_remove()
    ttk.Label(main, textvariable=owner.operation_status, style='App.TLabel', foreground=COLORS['muted'], font=(UI_FONT, 9)).grid(row=8, column=0, sticky='w')
