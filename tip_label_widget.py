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

#global vars
mainWin = tk.Tk()

btn_value = 'XY'

radio_value = tk.StringVar()

combolist_text = tk.StringVar()

cache = {}

pic_handle = None

# functions

def extract_planes(dir, nrrd, eswc):
    array = sitk.GetArrayFromImage(sitk.ReadImage(os.path.join(dir, nrrd)))
    if eswc == None:
        mask = None
    else:
        n_skip = 0
        with open(os.path.join(dir, eswc), "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    n_skip += 1
                else:
                    break
        f.close()
        names = ["##n", "X", "Y", "Z", "parent"]
        mask = pd.read_csv(os.path.join(dir, eswc), index_col=0, skiprows=n_skip, sep=" ", usecols=[0, 2, 3, 4, 6], names=names)
    return np.max(array, axis=0), np.max(array, axis=2), np.max(array, axis=1), mask, 'na'

def refresh_controls(flag):
    btn['XY']['state'] = flag
    btn['YZ']['state'] = flag
    btn['XZ']['state'] = flag
    btn_left['state'] = flag
    btn_right['state'] = flag
    btn_save['state'] = flag
    radio_n['state'] = flag
    radio_na['state'] = flag
    radio_y['state'] = flag
    filemenu.entryconfig(1, state=flag)
    btn[btn_value].state(['pressed', 'disabled'])

def lf_btn_update(*arg):
    if combolist.current() == 0:
        btn_left.state(['disabled'])
    else:
        btn_left.state(['!disabled'])
    if combolist.current() == len(cache) - 1:
        btn_right.state(['disabled'])
    else:
        btn_right.state(['!disabled'])

def open_dir():
    dir = fd.askdirectory(title='Open a Directory..', mustexist=True)
    global cache
    if type(dir) != str or dir == '' or len(cache) != 0 and not mb.askokcancel(title='Continue?', message='Current cache will be overwritten.'):
        return
    files = os.listdir(dir)
    #TODO
    nrrd = {}
    for i in files:
        if i.endswith('.nrrd'):
            nrrd[i] = i.split('.')[0] + '.eswc'
            if not os.path.exists(os.path.join(dir, nrrd[i])):
                nrrd[i] = None
    cache = dict(zip(nrrd.keys(), [dict(zip( ('XY', 'YZ', 'XZ', 'mask', 'label'), extract_planes(dir, *i) )) for i in nrrd.items()] ))
    combolist['values'] = tuple(cache.keys())
    combolist.set('')
    if len(cache) > 0:
        refresh_controls('normal')
        combolist.current(0)
        lf_btn_update()
    else:
        refresh_controls('disabled')

def save_lab_as():
    path = fd.asksaveasfilename(title='Save Labels As..', filetypes=[('CSV file ', '*.csv'), ('Excel file', '*.xls;*.xlsx')])
    if type(path) != str or path == '':
        return
    df = pd.DataFrame(np.array([(i, j['label']) for i, j in cache.items()]), columns=['filename', 'label']).set_index('filename')
    if path.endswith('.csv'):
        df.to_csv(path, sep=' ')
    elif path.endswith('.xls') or path.endswith('.xlsx'):
        df.to_excel(path, sep=' ')

def about():
    mb.showinfo(title='About Tip Label Tool', message='Developed by ZZH for tip quality control')

def doc():
    mb.showerror(title='TODO', message='so sad')

def turn_plane(plane):
    global btn_value
    btn_value = plane
    for i, j in btn.items():
        j.state(['!pressed', '!disabled'])
    btn[plane].state(['pressed', 'disabled'])
    repaint()

def radio_update(*arg):
    if combolist_text.get() != '':
        radio_value.set(cache[combolist_text.get()]['label'])

def switch(direction):
    combolist.current(min(max(combolist.current() + direction, 0), len(cache) - 1))
    lf_btn_update()
    radio_update()

def judge():
    cache[combolist_text.get()]['label'] = radio_value.get()

def repaint(*args):
    view.delete('all')
    if combolist_text.get() != '':
        global pic_handle
        nrrd = cache[combolist_text.get()]
        temp = Image.fromarray(nrrd[btn_value])
        bias = view.winfo_width() // 2, view.winfo_height() // 2
        ratio = min(view.winfo_height() / temp.height, view.winfo_width() / temp.width)
        pic_handle = ImageTk.PhotoImage(temp.resize(size=(int(temp.width * ratio), int(temp.height * ratio)), resample=Image.BICUBIC))
        view.create_image(*bias, image=pic_handle)
        if nrrd['mask'] is not None:
            bias = bias[0] - temp.width * ratio // 2, bias[1] - temp.height * ratio // 2
            for index, row in nrrd['mask'].iterrows():
                if row['parent'] in nrrd['mask'].index:
                    view.create_line(*tuple([int(ratio * i + j) for i, j in zip(row[list(btn_value)], bias)]),
                                     *tuple([int(ratio * i + j) for i, j in zip(nrrd['mask'].loc[row['parent'], list(btn_value)], bias)]), 
                                     fill='green')

def set_v3d_path():
    pass

def display_on_v3d():
    pass

# mainwindow
mainWin.title('Tip Label Tool')
style = ttk.Style(mainWin)
scr_size = mainWin.winfo_screenwidth(), mainWin.winfo_screenheight()
style.configure('XYZ.TButton', font=('Helvetica', scr_size[1] // 32, 'bold'))
style.configure('LF.TButton', font=('Helvetica', scr_size[1] // 16, 'bold'))
mainWin.geometry('%dx%d+%d+%d' % (scr_size[0] // 2, scr_size[1] // 2, scr_size[0] // 4, scr_size[1] // 4))
mainWin.minsize(scr_size[0] // 2, scr_size[1] // 2)

# menubar
menubar = tk.Menu(mainWin)
filemenu = tk.Menu(menubar, tearoff=False)
helpmenu = tk.Menu(menubar, tearoff=False)
toolmenu = tk.Menu(menubar)
menubar.add_cascade(label='File', menu=filemenu)
filemenu.add_command(label='Open a dir..', command=open_dir)
filemenu.add_command(label='Save labels as..', command=save_lab_as, state='disabled')
filemenu.add_separator()
filemenu.add_command(label='Exit', command=mainWin.quit)
menubar.add_cascade(label='Tool', menu=toolmenu)
toolmenu.add_command(label='Set Vaa3D path..', command=set_v3d_path)
toolmenu.add_command(label='Display on Vaa3D', command=display_on_v3d, state='disabled')
menubar.add_cascade(label='Help', menu=helpmenu)
helpmenu.add_command(label='About', command=about)
helpmenu.add_command(label='Documentation', command=doc)

# upper
frame_up = tk.LabelFrame(mainWin, text='Plane Panel', height=scr_size[1] // 10)
frame_up.pack(fill='x', expand='no', padx=10, pady=10)
frame_up.pack_propagate(0)
btn = {}
btn['XY'] = ttk.Button(frame_up, text='XY', command=lambda : turn_plane('XY'), style='XYZ.TButton', state='disabled')
btn['YZ'] = ttk.Button(frame_up, text='YZ', command=lambda : turn_plane('YZ'), style='XYZ.TButton', state='disabled')
btn['XZ'] = ttk.Button(frame_up, text='XZ', command=lambda : turn_plane('XZ'), style='XYZ.TButton', state='disabled')
btn['XY'].pack(side='left', expand='yes', fill='both', padx=10, pady=10)
btn['XZ'].pack(side='right', expand='yes', fill='both', padx=10, pady=10)
btn['YZ'].pack(side='left', expand='yes', fill='both', pady=10)

# middle
frame_mid = tk.Frame(mainWin)
frame_mid.pack(fill='both', expand='yes', padx=10, pady=10)
frame_mid.pack_propagate(0)
frame_left = tk.Frame(frame_mid, width=scr_size[0] // 20)
frame_right = tk.Frame(frame_mid, width=scr_size[0] // 20)
frame_canvas = tk.LabelFrame(frame_mid, width=scr_size[0] * 2 // 3)
frame_left.pack(side='left', expand='yes', anchor='e', fill='y')
frame_right.pack(side='right', expand='yes', anchor='w', fill='y')
frame_canvas.pack(side='left', expand='yes', fill='both')
frame_left.pack_propagate(0)
frame_right.pack_propagate(0)
frame_canvas.pack_propagate(0)
btn_left = ttk.Button(frame_left, text='<', command=lambda : switch(-1), style='LF.TButton', state='disabled')
btn_right = ttk.Button(frame_right, text='>', command=lambda : switch(1), style='LF.TButton', state='disabled')
btn_left.pack(expand='yes', fill='both')
btn_right.pack(expand='yes', fill='both')
view = tk.Canvas(frame_canvas)
view.bind('<Configure>', repaint)
view.pack(expand='yes', fill='both')

# downer
frame_down = tk.LabelFrame(mainWin, text='Control Panel', height = scr_size[1] // 16)
frame_down.pack(side='bottom', fill='x', expand='no', anchor='s', padx=10, pady=10)
frame_down.pack_propagate(0)
combolabel = tk.Label(frame_down, text='Sorted .nrrd files: ', font=('Arial', scr_size[1] // 80))
combolabel.pack(side='left', padx=10)
combolist = ttk.Combobox(frame_down, width=scr_size[0], state='readonly', textvariable=combolist_text)
btn_open = tk.Button(frame_down, text='Open', command=open_dir)
btn_save = tk.Button(frame_down, text='Save', command=save_lab_as, state='disabled')
btn_save.pack(side='right', padx=10, fill='y', pady=10)
radio_y = tk.Radiobutton(frame_down, text='YES', state='disabled', font=('Arial', scr_size[1] // 80), command=judge, value='y', variable=radio_value)
radio_n = tk.Radiobutton(frame_down, text='NO', state='disabled', font=('Arial', scr_size[1] // 80), command=judge, value='n', variable=radio_value)
radio_na = tk.Radiobutton(frame_down, text='N/A', state='disabled', font=('Arial', scr_size[1] // 80), command=judge, value='na', variable=radio_value)
radio_na.pack(side='right', expand='yes', padx=10, pady=10)
radio_n.pack(side='right', expand='yes', padx=10, pady=10)
radio_y.pack(side='right', expand='yes', padx=10, pady=10)
btn_open.pack(side='right', padx=10, fill='y', pady=10)
combolist.pack(side='left', fill='y', pady=10)

# tracing and binding
combolist_text.trace_add(mode='write', callback=repaint)
combolist_text.trace_add(mode='write', callback=radio_update)
combolist_text.trace_add(mode='write', callback=lf_btn_update)

mainWin.config(menu=menubar)
mainWin.mainloop()
exit()