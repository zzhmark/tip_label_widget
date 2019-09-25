#importation
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog as fd
from tkinter import messagebox as mb

#importation from combine tip images
import SimpleITK as sitk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

#global vars
mainWin = tk.Tk()

mip_dict = {'XY':0, 'XZ':1, 'YZ':2}

button_value = 'XY'

radio_value = tk.StringVar()

filelist_value = tk.StringVar()

nrrd_cache = {}

pic_handle = np.array(0)

# functions

def extract_planes(nrrd):
    array = sitk.GetArrayFromImage(sitk.ReadImage(nrrd))
    return np.max(array, axis=0), np.max(array, axis=2), np.max(array, axis=1)

def refresh_controls(flag):
    button_xy['state'] = flag
    button_yz['state'] = flag
    button_xz['state'] = flag
    button_left['state'] = flag
    button_right['state'] = flag
    button_save['state'] = flag
    radio_n['state'] = flag
    radio_na['state'] = flag
    radio_y['state'] = flag

def open_from_dir():
    dir = fd.askdirectory(title='Open From Dir..', mustexist=True)
    if type(dir) != str or dir == '':
        return
    global judge
    global nrrds
    files = os.listdir(dir)
    nrrd_cache = dict(zip(i for i in files if i.endswith('.nrrd'), 
                     (zip(('XY', 'YZ', 'XZ', 'label'), (*extract_planes(nrrd), 'na')) for nrrd in (os.path.join(dir, i) for i in files if i.endswith('.nrrd')))))
    filelist['values'] = tuple(nrrd_cache.keys())
    filelist.set('')
    if len(nrrd_cache) > 0:
        refresh_controls('normal')
        filelist.current(0)
    else:
        refresh_controls('disabled')
#TODO
def save_lab_as():
    path = fd.asksaveasfilename(title='Save Labels As..', filetypes=[('CSV file ', '*.csv'), ('Excel file', '*.xls;*.xlsx')])
    df = pd.DataFrame(data=judge)

def about():
    mb.showinfo(title='About Tip Label Tool', message='Developed by ZZH for tip quality control')

def doc():
    mb.showerror(title='TUDO', message='so sad')

def turn_plane(plane):
    global button_value
    button_value = plane

def switch(direction):
    filelist.current(filelist.current() + direction)
    global radio_value
    radio_value = judge[filelist_value.get()]     

def judgement():
    judge[filelist_value.get()] = radio_value

# TOD
def filelist_callback():
    if filelist_value.get() != '':
        pic_handle = nrrd_cache[filelist_value.get()][button_value]


filelist_value.trace('w', filelist_callback)

# mainwindow
mainWin.title('Tip Label Tool')
scr_size = mainWin.winfo_screenwidth(), mainWin.winfo_screenheight()
mainWin.geometry('%dx%d+%d+%d' % (scr_size[0] // 2, scr_size[1] // 2, scr_size[0] // 4, scr_size[1] // 4))
mainWin.minsize(scr_size[0] // 2, scr_size[1] // 2)

# menubar
menubar = tk.Menu(mainWin)
filemenu = tk.Menu(menubar, tearoff=False)
helpmenu = tk.Menu(menubar, tearoff=False)
menubar.add_cascade(label='File', menu=filemenu)
filemenu.add_command(label='Open from dir..', command=open_from_dir)
filemenu.add_command(label='Save labels as..', command=save_lab_as, state='disabled')
menubar.add_cascade(label='Help', menu=helpmenu)
helpmenu.add_command(label='About me', command=about)
helpmenu.add_command(label='Documentation', command=doc)

# upper
frame_up = tk.LabelFrame(mainWin, text='Plane Panel', height=scr_size[1] // 10)
frame_up.pack(fill='x', expand='no', padx=10, pady=10)
frame_up.pack_propagate(0)
button_xy = tk.Button(frame_up, text='XY', command=lambda : turn_plane('XY'), font='Helvetica %d bold' % (scr_size[1] // 32), state='disabled')
button_yz = tk.Button(frame_up, text='YZ', command=lambda : turn_plane('YZ'), font='Helvetica %d bold' % (scr_size[1] // 32), state='disabled')
button_xz = tk.Button(frame_up, text='XZ', command=lambda : turn_plane('XZ'), font='Helvetica %d bold' % (scr_size[1] // 32), state='disabled')
button_xy.pack(side='left', expand='yes', fill='both', padx=10, pady=10)
button_xz.pack(side='right', expand='yes', fill='both', padx=10, pady=10)
button_yz.pack(side='left', expand='yes', fill='both', pady=10)

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
button_left = tk.Button(frame_left, text='<', command=lambda : switch(-1), font='Helvetica %d bold' % (scr_size[1] // 16), state='disabled')
button_right = tk.Button(frame_right, text='>', command=lambda : switch(1), font='Helvetica %d bold' % (scr_size[1] // 16), state='disabled')
button_left.pack(expand='yes', fill='both')
button_right.pack(expand='yes', fill='both')
view = tk.Canvas(frame_canvas)
view.create_bitmap(pic_handle)
view.pack(expand='yes', fill='both')

# downer
frame_down = tk.LabelFrame(mainWin, text='Control Panel', height = scr_size[1] // 16)
frame_down.pack(side='bottom', fill='x', expand='no', anchor='s', padx=10, pady=10)
frame_down.pack_propagate(0)
combolabel = tk.Label(frame_down, text='Sorted .nrrd files: ', font=('Arial', scr_size[1] // 80))
combolabel.pack(side='left', padx=10)
filelist = ttk.Combobox(frame_down, width=scr_size[0], state='readonly', textvariable=filelist_value)
button_open = tk.Button(frame_down, text='Open', command=open_from_dir)
button_save = tk.Button(frame_down, text='Save', command=save_lab_as, state='disabled')
button_save.pack(side='right', padx=10, fill='y', pady=10)
radio_y = tk.Radiobutton(frame_down, text='YES', state='disabled', font=('Arial', scr_size[1] // 80), command=judgement, value='y', variable=radio_value)
radio_n = tk.Radiobutton(frame_down, text='NO', state='disabled', font=('Arial', scr_size[1] // 80), command=judgement, value='n', variable=radio_value)
radio_na = tk.Radiobutton(frame_down, text='N/A', state='disabled', font=('Arial', scr_size[1] // 80), command=judgement, value='na', variable=radio_value)
radio_na.pack(side='right', expand='yes', padx=10, pady=10)
radio_n.pack(side='right', expand='yes', padx=10, pady=10)
radio_y.pack(side='right', expand='yes', padx=10, pady=10)
button_open.pack(side='right', padx=10, fill='y', pady=10)
filelist.pack(side='left', fill='y', pady=10)

mainWin.config(menu=menubar)
mainWin.mainloop()
exit()