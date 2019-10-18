#importation
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from PIL import Image, ImageTk
import SimpleITK as sitk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import threading

lock = threading.RLock()

class progress_popup(tk.Toplevel):
    
    def __init__(self, master, text=''):
        self._flag = True
        tk.Toplevel.__init__(self, master=master)
        self.geometry('%dx%d+%d+%d' % (master.winfo_screenwidth() // 4, 
                                        master.winfo_screenwidth() // 16, 
                                        master.winfo_rootx() + master.winfo_width() // 2 - master.winfo_screenwidth() // 8, 
                                        master.winfo_rooty() + master.winfo_height() // 2 - master.winfo_screenwidth() // 32
                                        )
                        )
        self.attributes('-topmost', True)
        self.resizable(width=False, height=False)
        label = tk.Label(self, text=text)
        self._probar = ttk.Progressbar(self, 
                                        length = master.winfo_screenwidth(), 
                                        mode='determinate', 
                                        orient='horizontal'
                                        )
        self._probar['value'] = 0
        label.pack(padx=20, pady=20)
        self._probar.pack(padx=20, pady=20)
        self.grab_set()

    def maximum(self, max):
        self._probar['maximum'] = max

    def step(self):
        self._probar.step()
        self._probar.update()
    
    def destroy(self):
        lock.acquire()
        self._flag = False
        lock.release()
        super().destroy()

class type_dialog(tk.Toplevel):

    def __init__(self, master=None, title='', types=('NULL',)):
        tk.Toplevel.__init__(self, master=master)
        self.attributes('-topmost', True)
        self.resizable(width=False, height=False)
        self._label = tk.Label(self, text='Please choose a(n) '+title+' type: ')
        self._typelist = ttk.Combobox(self, 
                                        width=self.winfo_width(), 
                                        state='readonly', 
                                        )
        self._typelist['value'] = types
        self._typelist.current(0)
        self._btn = tk.Button(self,
                                text='OK', 
                                command=self._ok, 
                                )
        self._label.pack(fill='both', padx=20, pady=10)
        self._typelist.pack(fill='both', padx=20)
        self._btn.pack(fill='both', padx=20, pady=10)
        self.geometry('%dx%d+%d+%d' % (master.winfo_screenwidth() // 8, 
                                        master.winfo_screenwidth() // 16, 
                                        master.winfo_rootx() + master.winfo_width() // 2 - master.winfo_screenwidth() // 16, 
                                        master.winfo_rooty() + master.winfo_height() // 2 - master.winfo_screenwidth() // 32
                                        )
                        )
        self.grab_set()
        self._type = None
    
    def _ok(self):
        self._type = self._typelist.get()
        self.destroy()

class BLW(tk.Tk):
    #class members
    _axis_color = {'X':'#f00', 'Y':'#0f0', 'Z':'#00f'}
    _plane_to_no = {'XY':0, 'YZ':1, 'XZ':2}
    _no_to_plane = 'XY', 'YZ', 'XZ'

    def __init__(self):
        tk.Tk.__init__(self)
        #object vars
        self._btn_value = 'XY'
        self._radio_var = tk.StringVar()
        self._surf_on = tk.BooleanVar()
        self._axes_on = tk.BooleanVar()
        self._combolist_text = tk.StringVar()
        self._cache = {}
        self._pic_handle = None
        self._path_v3d = ''
        self._dir = None
        self._btn = {}
        self._radio = {}
        self._menu = {}
        self._rawtype = None
        self._masktype = None
        frame = {}
        # mainwindow
        self.title('Batch Label Widget')
        style = ttk.Style(self)
        scrw, scrh = self.winfo_screenwidth(), self.winfo_screenheight()
        style.configure('XYZ.TButton', 
                        font=('Helvetica', scrh//32, 'bold')
                        )
        style.configure('LF.TButton', 
                        font=('Helvetica', scrh//16, 'bold')
                        )
        self.geometry('%dx%d+%d+%d' % (scrw//2, scrh//2, scrw//4, scrh//4))
        self.minsize(scrw//2, scrh//2)
        # menubar
        menubar = tk.Menu(self)
        self._menu['file'] = tk.Menu(menubar, tearoff=False)
        self._menu['tool'] = tk.Menu(menubar, tearoff=False)
        self._menu['help'] = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='File', menu=self._menu['file'])
        menubar.add_cascade(label='Tool', menu=self._menu['tool'])
        menubar.add_cascade(label='Help', menu=self._menu['help'])
        self._menu['file'].add_command(label='Open a dir..', 
                                        command=self._open_dir, 
                                        accelerator='Ctrl+O'
                                        )
        self._menu['file'].add_command(label='Save labels as..', 
                                        command=self._save_as, 
                                        state='disabled', 
                                        accelerator='Ctrl+S'
                                        )
        self._menu['file'].add_separator()
        self._menu['file'].add_command(label='Exit', command=self.destroy)
        self._menu['tool'].add_command(label='Set Vaa3D path..', command=self._set_v3d_path)
        self._menu['tool'].add_command(label='Display on Vaa3D', 
                                        command=self._display_on_v3d, 
                                        accelerator='Ctrl+V'
                                        )
        self._menu['help'].add_command(label='About', command=BLW._about)
        self.config(menu=menubar)
        # upper
        frame['up'] = tk.LabelFrame(self, 
                                    text='Plane Panel', 
                                    height=scrh // 10
                                    )
        frame['up'].pack(fill='x', 
                            expand='no', 
                            padx=10, 
                            pady=10
                            )
        frame['up'].pack_propagate(0)
        self._btn['XY'] = ttk.Button(frame['up'], 
                                        text='XY', 
                                        command=lambda : self._turn_plane(plane='XY'), 
                                        style='XYZ.TButton', 
                                        state='disabled'
                                        )
        self._btn['YZ'] = ttk.Button(frame['up'], 
                                        text='YZ', 
                                        command=lambda : self._turn_plane(plane='YZ'), 
                                        style='XYZ.TButton', 
                                        state='disabled'
                                        )
        self._btn['XZ'] = ttk.Button(frame['up'], 
                                        text='XZ', 
                                        command=lambda : self._turn_plane(plane='XZ'), 
                                        style='XYZ.TButton', 
                                        state='disabled'
                                        )
        self._btn['XY'].pack(side='left', 
                                expand='yes', 
                                fill='both', 
                                padx=10, 
                                pady=10
                                )
        self._btn['XZ'].pack(side='right', 
                                expand='yes', 
                                fill='both', 
                                padx=10, 
                                pady=10
                                )
        self._btn['YZ'].pack(side='left', 
                                expand='yes', 
                                fill='both', 
                                pady=10
                                )
        # middle
        frame['mid'] = tk.Frame(self)
        frame['mid'].pack(fill='both', 
                            expand='yes', 
                            padx=10, 
                            pady=10
                            )
        frame['mid'].pack_propagate(0)
        frame['left'] = tk.Frame(frame['mid'], width=scrw//20)
        frame['right'] = tk.Frame(frame['mid'], width=scrw//20)
        frame['canvas'] = tk.LabelFrame(frame['mid'], width=scrw*2//3)
        frame['left'].pack(side='left', 
                            expand='yes', 
                            anchor='e', 
                            fill='y'
                            )
        frame['right'].pack(side='right', 
                            expand='yes', 
                            anchor='w', 
                            fill='y'
                            )
        frame['canvas'].pack(side='left', 
                                expand='yes', 
                                fill='both'
                                )
        frame['left'].pack_propagate(0)
        frame['right'].pack_propagate(0)
        frame['canvas'].pack_propagate(0)
        self._btn['left'] = ttk.Button(frame['left'], 
                                        text='<', 
                                        command=lambda : self._switch(-1), 
                                        style='LF.TButton', 
                                        state='disabled'
                                        )
        self._btn['right'] = ttk.Button(frame['right'], 
                                        text='>', 
                                        command=lambda : self._switch(1), 
                                        style='LF.TButton', 
                                        state='disabled'
                                        )
        self._btn['left'].pack(expand='yes', fill='both')
        self._btn['right'].pack(expand='yes', fill='both')
        self._view = tk.Canvas(frame['canvas'])
        self._view.pack(expand='yes', fill='both')
        # downer
        frame['down'] = tk.LabelFrame(self, 
                                        text='Control Panel', 
                                        height = scrh // 16
                                        )
        frame['down'].pack(side='bottom', 
                            fill='x', 
                            expand='no', 
                            anchor='s', 
                            padx=10, 
                            pady=10
                            )
        frame['down'].pack_propagate(0)
        combolabel = tk.Label(frame['down'], 
                                text='Samples: ', 
                                font=('Arial', scrh//80)
                                )
        combolabel.pack(side='left', padx=10)
        self._combolist = ttk.Combobox(frame['down'], 
                                        width=scrw, 
                                        state='readonly', 
                                        textvariable=self._combolist_text
                                        )
        self._btn['open'] = tk.Button(frame['down'], 
                                        text='Open', 
                                        command=self._open_dir
                                        )
        self._btn['save'] = tk.Button(frame['down'], 
                                        text='Save', 
                                        command=self._save_as, 
                                        state='disabled'
                                        )
        self._btn['save'].pack(side='right', 
                                padx=10, 
                                fill='y', 
                                pady=10
                                )
        self._radio['y'] = tk.Radiobutton(frame['down'], 
                                            text='YES', 
                                            state='disabled', 
                                            font=('Arial', scrh//80), 
                                            command=self._judge, 
                                            value='y', 
                                            variable=self._radio_var
                                            )
        self._radio['n'] = tk.Radiobutton(frame['down'], 
                                            text='NO', 
                                            state='disabled', 
                                            font=('Arial', scrh//80), 
                                            command=self._judge, 
                                            value='n', 
                                            variable=self._radio_var
                                            )
        self._radio['na'] = tk.Radiobutton(frame['down'], 
                                            text='N/A', 
                                            state='disabled', 
                                            font=('Arial', scrh//80), 
                                            command=self._judge, 
                                            value='na', 
                                            variable=self._radio_var
                                            )
        # frame_check = tk.Frame(frame['down'])
        self._check_surf = tk.Checkbutton(frame['down'], 
                                            text='Surface', 
                                            state='disabled', 
                                            font=('Arial', scrh//80), 
                                            variable=self._surf_on
                                            )
        self._check_axes = tk.Checkbutton(frame['down'], 
                                            text='Axes', 
                                            state='disabled', 
                                            font=('Arial', scrh//80), 
                                            variable=self._axes_on
                                            )
        self._radio['na'].pack(side='right', 
                                expand='yes', 
                                padx=10, 
                                pady=10
                                )
        self._radio['n'].pack(side='right', 
                                expand='yes', 
                                padx=10, 
                                pady=10
                                )
        self._radio['y'].pack(side='right', 
                                expand='yes', 
                                padx=10, 
                                pady=10
                                )
        # frame_check.pack(side='right', expand='yes')
        self._check_surf.pack(side='right', 
                                expand='yes', 
                                padx=10, 
                                pady=10
                                )
        self._check_axes.pack(side='right', 
                                expand='yes', 
                                padx=10, 
                                pady=10
                                )
        self._btn['open'].pack(side='right', 
                                padx=10, 
                                fill='y', 
                                pady=10
                                )
        self._combolist.pack(side='left', 
                                fill='y', 
                                pady=10
                                )
        # tracing and binding
        self._combolist_text.trace_add(mode='write', callback=self._repaint)
        self._combolist_text.trace_add(mode='write', callback=self._radio_update)
        self._combolist_text.trace_add(mode='write', callback=self._check_update)
        self._combolist_text.trace_add(mode='write', callback=self._lf_btn_update)
        self._radio_var.trace_add(mode='write', callback=self._repaint_label)
        self._surf_on.trace_add(mode='write', callback=self._repaint)
        self._axes_on.trace_add(mode='write', callback=self._repaint)
        self._view.bind('<Configure>', self._repaint)
        self.bind('<MouseWheel>', self._scroll)
        self.bind('<Button-4>', self._scroll)
        self.bind('<Button-5>', self._scroll)
        self.bind('<Control-o>', self._key_open)
        self.bind('<Control-O>', self._key_open)
        self.bind('<Control-s>', self._key_save)
        self.bind('<Control-S>', self._key_save)
        self.bind('<Control-v>', self._key_v3d)
        self.bind('<Control-V>', self._key_v3d)
        self.bind('<Up>', self._key_switch)
        self.bind('<Down>', self._key_switch)
        self.bind('w', self._key_switch)
        self.bind('s', self._key_switch)
        self.bind('<Left>', self._key_turn_plane)
        self.bind('<Right>', self._key_turn_plane)
        self.bind('a', self._key_turn_plane)
        self.bind('d', self._key_turn_plane)
        self.bind('1', self._key_label)
        self.bind('2', self._key_label)
        self.bind('3', self._key_label)
        self.bind('j', self._key_label)
        self.bind('k', self._key_label)
        self.bind('l', self._key_label)
        self.bind('J', self._key_label)
        self.bind('K', self._key_label)
        self.bind('L', self._key_label)
        self.bind('q', self._key_axes)
        self.bind('Q', self._key_axes)
        self.bind('e', self._key_surf)
        self.bind('E', self._key_surf)

    @classmethod
    def _about(cls):
        mb.showinfo(title='About Batch Label Widget', message='Developed by ZZH for tip quality control')
    
    @classmethod
    def _extract_mask(cls, mask, masktype):
        if not os.path.exists(mask + masktype):
            return None
        n_skip = 0
        with open(mask + masktype, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    n_skip += 1
                else:
                    break
        names = ["##n", "X", "Y", "Z", "parent"]
        return pd.read_csv(mask + masktype, index_col=0, skiprows=n_skip, sep=" ", usecols=[0, 2, 3, 4, 6], names=names)

    @classmethod
    def _extract_raw(cls, raw, rawtype):
        img = sitk.ReadImage(raw + rawtype)
        if rawtype == '.tif':
            img = sitk.Flip(img, (False, True, False))
        array = sitk.GetArrayFromImage(img)
        # if len(array.shape) == 3:
        return np.max(array, axis=0), np.max(array, axis=2), np.max(array, axis=1)
        # else:
            # return array, np.zeros(array.shape), np.zeros(array.shape)

    def _ask_filetype(self, title, types):
        pop = type_dialog(self, title,  types)
        self.wait_window(pop)
        return pop._type
    
    def _check_update(self, *arg):
        self._surf_on.set(True)
        self._axes_on.set(True)

    def _display_on_v3d(self):
        if self._combolist_text.get() == '':
            return
        filename = os.path.join(self._dir, self._combolist_text.get())
        with open(filename + '.ano', 'w') as ano:
            ano.write('SWCFILE=' + filename + self._masktype + '\nRAWIMG=' + filename + self._rawtype)
            ano.close()
            try:
                if self._path_v3d == '':
                    raise
                os.system(self._path_v3d + ' "' + ano.name + '"')
            except:
                try:
                    os.system('vaa3d "' + ano.name + '"')
                except:
                    try:
                        os.system('vaa3d_msvc "' + ano.name + '"')
                    except:
                        mb.showerror(title='Vaa3D Not Found', message="Vaa3D executable isn't found in either the environment or the path specified.\n"
                                    "Please specify a proper path or add an environment path directing to an executable with a proper name."
                                    )
            os.remove(ano.name)

    def _judge(self):
        self._cache[self._combolist_text.get()]['label'] = self._radio_var.get()

    def _key_axes(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0:
            return
        self._axes_on.set(not self._axes_on.get())

    def _key_label(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0:
            return
        if event.keysym in ('1', 'j', 'J'):
            self._radio_var.set('y')
        elif event.keysym in ('2', 'k', 'K'):
            self._radio_var.set('n')
        else:
            self._radio_var.set('na')
        self._judge()

    def _key_open(self, event):
        if event.state & 1 == 0:
            self._open_dir()

    def _key_save(self, event):
        if event.state & 1 == 0 or \
            len(self._cache) == 0:
            self._save_as()

    def _key_surf(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0:
            return
        self._surf_on.set(not self._surf_on.get())

    def _key_v3d(self, event):
        if event.state & 1 == 0 or \
            len(self._cache) == 0:
            self._display_on_v3d()
    
    def _key_switch(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0 or \
                    event.widget is self._combolist or \
                        type(event.widget) == str and 'combobox' in event.wdiget:
            return
        if event.keysym in ('Up', 'w', 'W'):
            self._switch(-1)
        else:
            self._switch(1)

    def _key_turn_plane(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0:
            return
        if event.keysym in ('Right', 'd', 'D'):
            if self._btn_value != 'XZ':
                self._turn_plane(self._no_to_plane[min(self._plane_to_no[self._btn_value] + 1, 2)]
                                )
        else:
            if self._btn_value != 'XY':
                self._turn_plane(self._no_to_plane[max(self._plane_to_no[self._btn_value] - 1, 0)]
                                )

    def _lf_btn_update(self, *arg):
        if self._combolist.current() == 0:
            self._btn['left'].state(['disabled'])
        else:
            self._btn['left'].state(['!disabled'])
        if self._combolist.current() == len(self._cache) - 1:
            self._btn['right'].state(['disabled'])
        else:
            self._btn['right'].state(['!disabled'])

    def _load_files(self, dir, rawtype, masktype):
        pop = progress_popup(self, 'Loading from ' + dir + '..')
        lock.acquire()
        if not pop._flag:
            return None
        cache = {i.replace(rawtype,''): dict.fromkeys(('XY','YZ','XZ','mask','label')) 
                    for i in os.listdir(dir) if i.endswith(rawtype)
                    }
        pop.maximum(len(cache) + 1)
        lock.release()
        for i, j in cache.items():
            lock.acquire()
            if not pop._flag:
                return None
            j['XY'], j['YZ'], j['XZ'] = BLW._extract_raw(os.path.join(dir, i), rawtype)
            j['mask'] = BLW._extract_mask(os.path.join(dir, i), masktype)
            j['label'] = ''
            pop.step()
            lock.release()
        lock.acquire()
        if not pop._flag:
            return None
        pop.destroy()
        lock.release()
        return cache

    def _open_dir(self):
        temp = fd.askdirectory(title='Open a Directory..', mustexist=True)
        if type(temp) != str or temp == '' or len(self._cache) != 0 and \
            not mb.askokcancel(title='Continue?', message='Current cache will be overwritten.'):
            return
        rawtype = self._ask_filetype('raw image type', ('.tif', '.nrrd'))
        if rawtype is None:
            return
        masktype = self._ask_filetype('mask type', ('.eswc', '.swc'))
        if rawtype is None:
            return
        cache = self._load_files(temp, rawtype, masktype)
        if cache is None:
            return
        self._combolist['values'] = tuple(cache.keys())
        self._combolist.set('')
        self._dir = temp
        self._cache = cache
        if len(cache) > 0:
            self._rawtype = rawtype
            self._masktype = masktype
            self._refresh_controls('normal')
            self._combolist.current(0)
            self._lf_btn_update()
        else:
            self._refresh_controls('disabled')
            self._pic_handle = None

    def _radio_update(self, *arg):
        if self._combolist_text.get() != '':
            self._radio_var.set(self._cache[self._combolist_text.get()]['label'])

    def _refresh_controls(self, flag):
        self._btn['XY']['state'] = flag
        self._btn['YZ']['state'] = flag
        self._btn['XZ']['state'] = flag
        self._btn['left']['state'] = flag
        self._btn['right']['state'] = flag
        self._btn['save']['state'] = flag
        self._radio['n']['state'] = flag
        self._radio['na']['state'] = flag
        self._radio['y']['state'] = flag
        self._check_surf['state'] = flag
        self._check_axes['state'] = flag
        self._menu['file'].entryconfig(1, state=flag)
        self._menu['tool'].entryconfig(1, state=flag)
        self._btn[self._btn_value].state(['pressed', 'disabled'])

    def _repaint(self, *arg):
        self._view.delete('all')
        if self._combolist_text.get() == '':
            return
        raw = self._cache[self._combolist_text.get()]
        temp = Image.fromarray(raw[self._btn_value])
        view_w, view_h = self._view.winfo_width(), self._view.winfo_height()
        bias_center = view_w // 2, \
                        view_h // 2
        ratio = min(view_w / temp.height, 
                    view_h / temp.width
                    )
        paint_size = int(temp.width*ratio), int(temp.height*ratio)
        self._pic_handle = ImageTk.PhotoImage(temp.resize(size=paint_size, resample=Image.BICUBIC)
                                        )
        self._view.create_image(*bias_center, 
                                image=self._pic_handle, 
                                tag='img'
                                )
        bias_tl = bias_center[0] - paint_size[0] // 2, \
                    bias_center[1] - paint_size[1] // 2
        if self._axes_on.get():
            self._view.create_line(bias_tl[0], 
                                    bias_center[1], 
                                    bias_tl[0] + paint_size[0], 
                                    bias_center[1], 
                                    fill=BLW._axis_color[self._btn_value[0]], 
                                    width=1, 
                                    arrow='last', 
                                    arrowshape='%d %d %d'%(paint_size[0]//200, paint_size[0]//100, paint_size[0]//200), 
                                    dash=1, 
                                    tag='axis'
                                    )
            self._view.create_text(bias_tl[0] + paint_size[0], 
                                    bias_center[1], 
                                    text=self._btn_value[0], 
                                    anchor='ne', 
                                    fill='white', 
                                    font=('Arial', max(min(paint_size[0]//40, 15), 10)), 
                                    tag='axis'
                                    )
            self._view.create_line(bias_center[0], 
                                    bias_tl[1], 
                                    bias_center[0], 
                                    bias_tl[1] + paint_size[1], 
                                    fill=BLW._axis_color[self._btn_value[1]], 
                                    width=1, 
                                    arrow='last', 
                                    arrowshape='%d %d %d'%(paint_size[0]//200, paint_size[0]//100, paint_size[0]//200), 
                                    dash=1, 
                                    tag='axis'
                                    )
            self._view.create_text(bias_center[0], 
                                    bias_tl[1] + paint_size[1], 
                                    text=self._btn_value[1], 
                                    anchor='se', 
                                    fill='white', 
                                    font=('Arial', max(min(paint_size[0] // 40, 15), 10)), 
                                    tag='axis'
                                    )
        if raw['mask'] is not None and self._surf_on.get():
            for index, row in raw['mask'].iterrows():
                if row['parent'] in raw['mask'].index:
                    self._view.create_line(*tuple([int(ratio * i + j) 
                                                    for i, j in zip(row[list(self._btn_value)], bias_tl)
                                                    ]),
                                            *tuple([int(ratio * i + j) 
                                                    for i, j in zip(raw['mask'].loc[row['parent'], list(self._btn_value)], bias_tl)
                                                    ]), 
                                            fill='#fb0', 
                                            width=2, 
                                            tag='mask'
                                            )
        self._view.create_text(bias_tl, 
                                text='#%d' % (self._combolist.current()+1), 
                                fill='white', 
                                anchor='nw'
                                )
        self._repaint_label()

    def _repaint_label(self, *arg):
        if len(self._cache) == 0 or self._pic_handle == None:
            return
        self._view.delete('label')
        length = self._pic_handle.width() // 10
        pad = self._pic_handle.width() // 100
        anchor = (self._view.winfo_width() + self._pic_handle.width()) // 2
        if self._radio_var.get() == 'y':
            self._view.create_line(anchor - pad - length, 
                                    pad + length // 2, 
                                    anchor - pad, 
                                    pad + length // 2, 
                                    fill='#0f0', 
                                    tag='label', 
                                    width = pad
                                    )
            self._view.create_line(anchor - pad - length // 2, 
                                    pad, 
                                    anchor - pad - length // 2, 
                                    pad + length, 
                                    fill='#0f0', 
                                    tag='label', 
                                    width = pad
                                    )
        elif self._radio_var.get() == 'n':
            self._view.create_line(anchor - pad - length, 
                                    pad + length // 2, 
                                    anchor - pad, 
                                    pad + length // 2, 
                                    fill='#f00', 
                                    tag='label', 
                                    width = pad
                                    )
        elif self._radio_var.get() == 'na':
            self._view.create_text(anchor - pad, 
                                    -pad, 
                                    text='?', 
                                    anchor='ne', 
                                    font=('Arial', length), 
                                    fill='#ff0', 
                                    tag='label'
                                    )

    def _save_as(self):
        if len(self._cache) == 0:
            return
        path = fd.asksaveasfilename(title='Save Labels As..', 
                                    filetypes=[('CSV file ', '*.csv'), 
                                    ('Excel file', '*.xls;*.xlsx')], 
                                    defaultextension='*.*'
                                    )
        if type(path) != str or path == '':
            return
        df = pd.DataFrame(np.array([(i, j['label']) 
                                    for i, j in self._cache.items()
                                    ]), 
                            columns=['filename', 'label']
                            ).set_index('filename')
        if path.endswith('.csv'):
            df.to_csv(path, sep=' ')
        elif path.endswith('.xls') or path.endswith('.xlsx'):
            df.to_excel(path, sep=' ')

    def _scroll(self, event):
        if len(self._cache) == 0 or \
            event.widget is self._combolist or \
            type(event.widget) == str and 'combobox' in event.widget:
            return
        elif event.num == 4 or event.delta == 120:
            self._switch(-1)
        else:
            self._switch(1)
        self._lf_btn_update()
        self._radio_update()

    def _set_v3d_path(self):
        temp = fd.askopenfilename(title='Input the Path to a Vaa3D Executable..', initialdir=self._path_v3d)
        if type(temp) != str or temp == '':
            return
        self._path_v3d = temp

    def _switch(self, direction):
        if 0 <= self._combolist.current() + direction < len(self._cache):
            self._turn_plane('XY')
        self._combolist.current(min(max(self._combolist.current() + direction, 0), 
                                    len(self._cache) - 1
                                    )
                                )
        self._lf_btn_update()
        self._radio_update()

    def _turn_plane(self, plane):
        self._btn_value = plane
        self._btn['XY'].state(['!pressed', '!disabled'])
        self._btn['YZ'].state(['!pressed', '!disabled'])
        self._btn['XZ'].state(['!pressed', '!disabled'])
        self._btn[plane].state(['pressed', 'disabled'])
        self._repaint()

if __name__ == "__main__":
    app = BLW()
    app.mainloop()