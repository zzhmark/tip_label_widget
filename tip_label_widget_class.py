#importation
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from PIL import Image, ImageTk

#importation from combine tip images
import SimpleITK as sitk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

class tip_label_widget(tk.Tk):
    
    #class constant
    _axis_color = {'X':'#f00', 'Y':'#0f0', 'Z':'#00f'}
    _plane_to_no = {'XY':0, 'YZ':1, 'XZ':2}
    _no_to_plane = 'XY', 'YZ', 'XZ'

    def __init__(self):
        tk.Tk.__init__(self)
        #object vars
        self._btn_value = 'XY'
        self._radio_var = tk.StringVar()
        self._combolist_text = tk.StringVar()
        self._cache = {}
        self._pic_handle = None
        self._path_v3d = ''
        self._dir = None
        self._load_label_text = tk.StringVar()
        self._btn = {}
        self._radio = {}
        self._menu = {}
        frame = {}
        # mainwindow
        self.title('Tip Label Tool')
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
        self._menu['help'].add_command(label='About', command=tip_label_widget._about)
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
                                text='Sorted .nrrd files: ', 
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
                                    font=('Arial', 
                                    scrh // 80), 
                                    command=self._judge, 
                                    value='na', 
                                    variable=self._radio_var
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
        self._btn['open'].pack(side='right', 
                        padx=10, 
                        fill='y', 
                        pady=10
                        )
        self._combolist.pack(side='left', 
                            fill='y', 
                            pady=10
                            )
        # popup
        self._load_pop = tk.Toplevel(self)
        self._load_pop.withdraw()
        self._load_pop.overrideredirect(True)
        self._load_pop.attributes('-topmost', True)
        self._load_pop.resizable(width=False, height=False)
        load_label = tk.Label(self._load_pop, textvariable=self._load_label_text)
        self._load_pro = ttk.Progressbar(self._load_pop, 
                                            length=scrw // 4, 
                                            mode='determinate', 
                                            orient='horizontal'
                                            )
        load_label.pack(padx=20, pady=20)
        self._load_pro.pack(padx=20, pady=20)
        # tracing and binding
        self._combolist_text.trace_add(mode='write', callback=self._repaint)
        self._combolist_text.trace_add(mode='write', callback=self._radio_update)
        self._combolist_text.trace_add(mode='write', callback=self._lf_btn_update)
        self._radio_var.trace_add(mode='write', callback=self._repaint_label)
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



    # static functions
    def _about():
        mb.showinfo(title='About Tip Label Tool', message='Developed by ZZH for tip quality control')
    
    def _extract_eswc(eswc):
        if os.path.exists(eswc):
            n_skip = 0
            with open(eswc, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith("#"):
                        n_skip += 1
                    else:
                        break
            names = ["##n", "X", "Y", "Z", "parent"]
            return pd.read_csv(eswc, index_col=0, skiprows=n_skip, sep=" ", usecols=[0, 2, 3, 4, 6], names=names)
        else:
            return None

    def _extract_nrrd(nrrd):
        array = sitk.GetArrayFromImage(sitk.ReadImage(nrrd))
        return np.max(array, axis=0), np.max(array, axis=2), np.max(array, axis=1)

    # object functions
    def _display_on_v3d(self):
        if self._combolist_text.get() == '':
            return
        filename = os.path.join(self._dir, self._combolist_text.get())
        with open(filename + '.ano', 'w') as ano:
            ano.write('SWCFILE=' + filename + '.eswc' + '\nRAWIMG=' + filename + '.nrrd')
            ano.close()
            print(ano.name)
            print(self._path_v3d)
            try:
                if self._path_v3d == '':
                    raise
                os.system(self._path_v3d + ' ' + ano.name)
            except:
                try:
                    os.system('vaa3d ' + ano.name)
                except:
                    try:
                        os.system('vaa3d_msvc ' + ano.name)
                    except:
                        mb.showerror(title='Vaa3D Not Found', message="Vaa3D executable isn't found in either the environment or the path specified.\n"
                                    "Please specify a proper path or add an environment path directing to an executable with a proper name."
                                    )
            os.remove(ano.name)

    def _judge(self):
        self._cache[self._combolist_text.get()]['label'] = self._radio_var.get()

    def _key_label(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0 or \
                self._load_pop.grab_status() is not None:
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
            len(self._cache) == 0 or \
                self._load_pop.grab_status() is not None:
            self._save_as()

    def _key_v3d(self, event):
        if event.state & 1 == 0 or \
            len(self._cache) == 0 or \
                self._load_pop.grab_status() is not None:
            self._display_on_v3d()
    
    def _key_switch(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0 or \
                self._load_pop.grab_status() is not None or \
                    event.widget is self._combolist or \
                        type(event.widget) == str and 'combobox' in event.wdiget:
            return
        if event.keysym in ('Up', 'w', 'W'):
            self._switch(-1)
        else:
            self._switch(1)

    def _key_turn_plane(self, event):
        if event.state & 5 > 0 or \
            len(self._cache) == 0 or \
            self._load_pop.grab_status() is not None:
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

    def _open_dir(self):
        temp = fd.askdirectory(title='Open a Directory..', mustexist=True)
        if type(temp) != str or temp == '' or len(self._cache) != 0 and \
            not mb.askokcancel(title='Continue?', message='Current cache will be overwritten.'):
            return
        self._load_pop.grab_set()
        self._load_label_text.set('Loading from ' + temp + '..')
        self._load_pro['value'] = 0
        self._load_pop.deiconify()
        self._dir = temp
        self._cache = {i.replace('.nrrd',''): dict.fromkeys(('XY','YZ','XZ','mask','label')) 
                        for i in os.listdir(temp) if i.endswith('.nrrd')
                        }
        self._load_pro['maximum'] = len(self._cache) + 1
        for i, j in self._cache.items():
            j['XY'], j['YZ'], j['XZ'] = tip_label_widget._extract_nrrd(os.path.join(temp, i+'.nrrd'))
            j['mask'] = tip_label_widget._extract_eswc(os.path.join(temp, i+'.eswc'))
            j['label'] = ''
            self._load_pro.step()
            self._load_pro.update()
        self._combolist['values'] = tuple(self._cache.keys())
        self._combolist.set('')
        if len(self._cache) > 0:
            self._refresh_controls('normal')
            self._combolist.current(0)
            self._lf_btn_update()
        else:
            self._refresh_controls('disabled')
            self._pic_handle = None
        self._load_pop.withdraw()
        self._load_pop.grab_release()

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
        self._menu['file'].entryconfig(1, state=flag)
        self._menu['tool'].entryconfig(1, state=flag)
        self._btn[self._btn_value].state(['pressed', 'disabled'])

    def _repaint(self, *arg):
        self._view.delete('img', 'axis', 'mask', 'all')
        if self._combolist_text.get() == '':
            return
        nrrd = self._cache[self._combolist_text.get()]
        temp = Image.fromarray(nrrd[self._btn_value])
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
        self._view.create_line(bias_tl[0], 
                                bias_center[1], 
                                bias_tl[0] + paint_size[0], 
                                bias_center[1], 
                                fill=tip_label_widget._axis_color[self._btn_value[0]], 
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
                                fill=tip_label_widget._axis_color[self._btn_value[1]], 
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
        if nrrd['mask'] is not None:
            for index, row in nrrd['mask'].iterrows():
                if row['parent'] in nrrd['mask'].index:
                    self._view.create_line(*tuple([int(ratio * i + j) 
                                                    for i, j in zip(row[list(self._btn_value)], bias_tl)
                                                    ]),
                                            *tuple([int(ratio * i + j) 
                                                    for i, j in zip(nrrd['mask'].loc[row['parent'], list(self._btn_value)], bias_tl)
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
            self._load_pop.grab_status() is not None or \
            event.widget is self.combolist or \
            type(event.widget) == str and 'combobox' in event.widget:
            return
        elif event.num == 4 or event.delta == 120:
            self._combolist.current(max(self._combolist.current() - 1, 0))
        else:
            self._combolist.current(min(self._combolist.current() + 1, len(self._cache) - 1))
        self._lf_btn_update()
        self._radio_update()

    def _set_v3d_path(self):
        temp = fd.askopenfilename(title='Input the Path to a Vaa3D Executable..', initialdir=self._path_v3d)
        if type(temp) != str or temp == '':
            return
        self._path_v3d = temp

    def _switch(self, direction):
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
    app = tip_label_widget()
    app.mainloop()