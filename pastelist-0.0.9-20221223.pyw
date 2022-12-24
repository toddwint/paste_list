#!/usr/bin/env python3
#!python3
'''
pastelist
Cross platform compatible application (Windows, macOS, and Linux)
Create a text list and paste the text line by line using a hotkey.
Commands can be captured from the system clipboard or from a text file.
There is an import option that allows vars in the file to be replaced with 
values from the user.
The list will cycle back around to the top after the last command which 
makes it easy to paste a bunch of commands on a whole bunch of devices.
This program was created to replace another software I was depending on but
which has not been updated since 2010 or 2012: 
  [ClipCycler](https://sourceforge.net/projects/clipcycler/).

- - -

Notes:

Windows
Just install Python from Python.org and install the required modules found
in the requirements.txt file. Open cmd in the same folder and type
`pip install -r requirements.txt`

macOS
Recommended to download Python from Python.org and install it. Don't use
the version of python that comes with macOS as it has issues with TCL/TK.
You'll also have to go into `Security & Privacy` > `Privacy` and add some
applications to `Input Monitoring`, `Accessibility`, `Automation`, and/or
`Developer Tools`. These applications might include `Terminal`, `IDLE.app`, `Python Launcher.app`, and `Python.app`. 
I disabled `System Integrity Protection`, but I don't really think that is 
needed.
You'll also need to install the required modules found in requirements.txt.

Linux 
Tested on Ubuntu 22.04 ($XDG_SESSION_TYPE=Wayland)
Linux is only working via Xorg at the moment which means you need to run
under Xorg or use a program that uses XWayland. Also keyboard suppression
is not currently implemented on Linux. You can modify this program to use
keys which aren't on the keyboard such as F13 and F14 in place of F3 and F4.
Then use xmodmap to map F3 and F4 to those keys. Or just find other F keys.
You'll also need to install the required modules found in requirements.txt.

Example file with vars <LANSW.vars.txt>:
#
#!os,KA_15_13_0008.swi,RA_15_16_0014m.swi
#!password,mygoodpass,secretpass,nopassword
config
vlan 1 ip address 10.1.1.2/24
copy tftp flash 10.1.1.1 %os% primary
y
reload
y
config
password manager plaintext %password%
password operator plaintext %password%
reload
y
n
'''

# To do:
#   add a logo
#   maybe check for comment lines and cycle past them
#   add a special character to conf files and move cursor to that position
#   remember the last used cycle forwards/backwards keys
#   add a help or about option
#   would it help to add a menu?
#   Maybe add key bindings, e.g. S for start/stop keybd listener, 
#    I import, H hookcb, R remote, C Clear, V vars
#   store full text import in variable so toggle allow blanks restores 
#    original blanks? but what about hook clipboard??
#
# Completed:
#   add or enter parameters with a textbox when importing files with vars
#   ESC on the child window stops the keylogger and doesn't close the child.
#   Add a button to stop/start keyboard listener
#
# Issues:
#   changing the cycle keys resets the list selection to the first value
#
# Resolved:
#   Will not paste (error) if trying to paste a blank line
#   sometimes it looses the input grabber (because you're pressing ESC)
#
# references:
#   https://docs.python.org/3/library/dialog.html
#   https://github.com/moses-palmer/pynput/issues/170
#   https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
#   https://pynput.readthedocs.io/en/latest/faq.html#how-do-i-suppress-specific-events-only

import pyperclip
import re
import sys
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.ttk, tkinter.messagebox, tkinter.filedialog

# PYNPUT BACKENDS (OPTIONAL)
# Backends are selected automatically. But you can override them.
# Configure these if you wish to set the backend manually.
# Delete this section if you do not.
#bkends_kybd = ['darwin', 'win32', 'uinput', 'xorg', 'dummy']
#bkends_mice = ['darwin', 'win32', 'xorg', 'dummy']

# Use PYNPUT_BACKEND if using same backend for keyboard and mouse
# More specific takes precedence if set
# PYNPUT_BACKEND_KEYBOARD & PYNPUT_BACKEND_MOUSE > PYNPUT_BACKEND
#bkend = 'xorg'
#os.environ['PYNPUT_BACKEND'] = bkend

# Use PYNPUT_BACKEND_KEYBOARD and PYNPUT_BACKEND_MOUSE to select per device
# More specific takes precedence if set
# PYNPUT_BACKEND_KEYBOARD & PYNPUT_BACKEND_MOUSE > PYNPUT_BACKEND
#bkend_kybd = 'uinput'
#bkend_mous = 'dummy'
#os.environ['PYNPUT_BACKEND_KEYBOARD'] = bkend_kybd
#os.environ['PYNPUT_BACKEND_MOUSE'] = bkend_mous

# uinput not working? It might not have found your keyboard device
# you can run this command to find your keyboard device
# sudo -E python3 -m evdev.evtest
# and then specify the device (example: /dev/input/event1)
# using the listener flag uinput_device_paths ['/dev/input/event0']

# import pynput after defining the backend
import pynput

def on_press(key):
    global keyforwardpressed
    global keyreversepressed
    if debug: print(f'PRESSED key={key}, type={type(key)}')
    if key == pynput.keyboard.Key[forward.get()]:
        if debug: print(forward.get(), 'key pressed')
        keyforwardpressed = True
    elif key == pynput.keyboard.Key[backward.get()]:
        if debug: print(backward.get(), 'key pressed')
        keyreversepressed = True
    else:
        pass # Nothing to do, Abe.

def on_release(key):
    global keyforwardpressed
    global keyreversepressed
    if debug: print(f'RELEASED key={key}, type={type(key)}')
    if key == pynput.keyboard.Key[forward.get()]:
        if debug: print(forward.get(), 'key released')
        keyforwardpressed = False
    elif key == pynput.keyboard.Key[backward.get()]:
        if debug: print(backward.get(), 'key released')
        keyreversepressed = False
    else:
        pass # Nothing to do, Abe.
    pass 

# https://github.com/moses-palmer/pynput/issues/170
# Windows has an event filter to suppress/block specific keys
# https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
# Mac OS does too
# Linux is a bit difficult. Either suppress all keys and manage all events
#  or don't. There is no filtering on individual keys.
#  Also, the backends are xorg and uinput. Xorg requires an X11 system or
#  an XWayland program. uinput requires root permissions.
#  The terminal on Ubuntu 22.04 is Wayland. I want to use the terminal.
#  The options are switch over to Xorg login or use a program that uses
#  XWayland. I settled on XWayland via a terminal inside of firefox with the
#  tool [ttyd](https://github.com/tsl0922/ttyd). Firefox is still XWayland.
#  You can verify this using the program `xeyes`.
#  I am currently not suppressing keys on linux. 
#  Firefox does not send the F3 and F4 keys through to the terminal. 
#  So at the moment, I do not need to suppress keys. For my use, it works.
#  When Wayland has the features needed and pynput is updated to include
#  these features this program should be updated to use those instead.

def win32_event_filter(msg, data):
    global listener
    if (msg == 0x0100 or msg == 0x0101) and (
        data.vkCode == keydict[forward.get()] or 
        data.vkCode == keydict[backward.get()]
        ): # Key Down/Up & selected cb cycle keys
        if debug: 
            print(f"Suppressing {forward.get()}/{backward.get()} up")
        listener._suppress = True
    #return False # comment...
        # if you return False, your on_press/on_release will not be called
    else:
        listener._suppress = False
        return True

def darwin_intercept(event_type, event):
    import Quartz
    length, chars = Quartz.CGEventKeyboardGetUnicodeString(
        event, 100, None, None)
    if length > 0 and (
        chars == forward.get() or chars == backward.get()
        ): # Suppress 
        return None
    else:  # nothing to do
        return event

def typeline_goforward():
    if l.curselection():
        try:
            curseltxt = l.selection_get()
        except:
            curseltxt = '' # can't select an empty string
        controller.type(curseltxt)
        cycleforward()
    if not l.curselection():
        print('Hey, no selection. Select a line first')

def typeline_gobackward():
    if l.curselection():
        try:
            curseltxt = l.selection_get()
        except:
            curseltxt = '' # can't select an empty string
        controller.type(curseltxt)
        cyclebackward()
    if not l.curselection():
        print('Hey, no selection. Select a line first')

def updatefwkey():
    if debug: print(forward.get())
    tmplist = list(l.get(0, "end"))
    if not tmplist: return
    l.selection_set(0)
    l.see(0)

def updatebwkey():
    if debug: print(backward.get())
    tmplist = list(l.get(0, "end"))
    if not tmplist: return
    l.selection_set(0)
    l.see(0)

def hookclipboard():
    global hookcbid
    global lastcbvalue
    if hookcb.get():
        lastcbvalue = ''
        pyperclip.copy('')
        checkcb()
    else:
        if hookcbid:
            root.after_cancel(hookcbid)
            hookcbid = ''

def additem(element):
    for line in element.replace('\r', '').rstrip().split('\n'): # comment...
        # blank lines are allowed but not last line (not catching \r chars)
    #for line in re.split(r'[\r\n]+', element): # comment...
        # no blank lines
    #for line in element.replace('\r','').split('\n'): # comment...
        #if you want blank lines
    #for line in re.split(r'\r?\n', element.rstrip()): # comment...
        # blank lines are allowed but not last line
        l.insert("end", line.lstrip()) # comment...
            # do we want to strip blank spaces and tabs?
    removeblanklines()
    
def removeitem():
    if l.curselection():
        curpos = l.curselection()[0]
        l.delete(l.curselection())
        if curpos < len(l.get(0, "end")):
            l.selection_set(curpos)
            l.see(curpos)
        elif curpos >= len(l.get(0, "end")):
            l.selection_set(len(l.get(0, "end"))-1)
            l.see(curpos)
        else:
            l.selection_set(0)
            l.see(0)
    else:
        print('No selection')
    
def clearclipboard():
    l.delete(0, "end")

def importcbfromfile():
    filename = tkinter.filedialog.askopenfilename(initialdir=".")
    if filename:
        print(filename)
        #tkinter.messagebox.showinfo(message=filename,title='selected file')
        with open(filename, 'r') as f:
            t = f.read()
        t = [x.lstrip() for x in re.split(r'\r?\n',t.rstrip())] # comment...
            # allow blank lines but not end line, 
            # remove leading spaces and tabs
        #t = re.split(r'[\r\n]+', t.rstrip()) # comment...
            # no blank lines
        clipboardlist.set(t)
        removeblanklines()
        if l.curselection():
            l.selection_clear(l.curselection())
        l.selection_set(0)
        l.see(0)
    else:
        print('No file selected')

def importcbfromvarfile():
    global childcombo
    global childvars
    filename = tkinter.filedialog.askopenfilename(initialdir=".")
    if filename:
        print(filename)
        #tkinter.messagebox.showinfo(message=filename,title='selected file')
        with open(filename, 'r') as f:
            t = f.read()
        importvarsdict = {
            x.strip('#!').split(',')[0]: x.split(',')[1:] 
            for x in t.split('\n') if x.startswith('#!')
            }
        if not importvarsdict:
            print("No variables found in file.")
        if not importvarsdict:
            tkinter.messagebox.showinfo(
                title="No variables found", 
                message=f"No variables found in file."
                )

        childvars = tk.Toplevel(root)
        childvars.title('Import list file with vars')
        mychild = ttk.Frame(childvars, padding=(6,12,6,12))
        mychild.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        childcombo = []
        childsels = []
        childentries = []

        ttk.Label(
            mychild, text='Variable'
            ).grid(
                column=1, row=1, padx=5, pady=5
                )
        ttk.Label(
            mychild, text='Select from list'
            ).grid(
                column=2, row=1, padx=5, pady=5
                )
        ttk.Label(
            mychild, text='Manually specify'
            ).grid(
                column=3, row=1, padx=5, pady=5
                )
  
        for n, (keyss, values) in enumerate(importvarsdict.items(),2):
            ttk.Label(
                mychild, text=f"{keyss}: "
                ).grid(
                    column=1, row=n, sticky=tk.E, padx=5, pady=10
                    )
            childsels.append(tk.StringVar())
            childsels[-1].set(values[-1])
            childcombo.append(ttk.Combobox(
                mychild, textvariable=childsels[-1], values=values
                ) )
            childcombo[-1].grid(
                column=2, row=n, sticky=tk.W, padx=5, pady=10
                )
            childentries.append(
                ttk.Entry(mychild, textvariable=childsels[-1])
                )
            childentries[-1].grid(
                column=3, row=n, sticky=tk.W, padx=5, pady=10
                )
     
        ttk.Button(mychild, text="Submit", command=(
            lambda: updatechildcombo(t,importvarsdict)
            )).grid(
                column=1, columnspan=3, row=n+1, rowspan=3, 
                sticky=(tk.E+tk.W+tk.N+tk.S)
                )

        childvars.bind("<Escape>", lambda event: childdismiss())
        childvars.bind("<Return>", lambda event: updatechildcombo(
            t,importvarsdict
            ))
        childvars.wait_visibility()
        childvars.grab_set()
        childvars.focus()
        childvars.wait_window()
    else:
        print('no file selected')
        return

def childdismiss():
    childvars.grab_release()
    childvars.destroy()

def updatechildcombo(t,importvarsdict):
    selectedvarslist = []
    for each in childcombo:
        selectedvarslist.append(each.get()) # comment...
            # get the current selected value of each combobox
    for n, (keyss, values) in enumerate(importvarsdict.items()):
        t = t.replace(f'%{keyss}%', selectedvarslist[n]) # comment...
            #replace the keyword var with the value
    t = [
        x.lstrip() for x in re.split(r'\r?\n', t.rstrip()) 
        if not x.startswith('#')
        ]   # comment...
        # allow blank lines but not end line, 
        # remove leading spaces and tabs
    #t = [ 
    #    x for x in re.split(r'[\r\n]+', t.rstrip()) 
    #    if not x.startswith('#')
    #    ] # comment...
    #    # do not allow blank lines
    clipboardlist.set(t)
    removeblanklines()
    if l.curselection():
        l.selection_clear(l.curselection())
    l.selection_set(0)
    l.see(0)
    childdismiss()
    childvars.destroy()
    return
    
def cycleforward():
    if debug: print('cycleforward')
    tmplist = list(l.get(0, "end"))
    if not tmplist: return
    if l.curselection():
        curpos = l.curselection()[0]
        if curpos < len(tmplist) - 1:
            l.selection_clear(curpos)
            l.selection_set(curpos+1)
            l.see(curpos+1)
        if curpos == len(tmplist) - 1:
            l.select_clear(curpos)
            l.selection_set(0)
            l.see(0)

def cyclebackward():
    if debug: print('cyclebackward')
    tmplist = list(l.get(0, "end"))
    if not tmplist: return
    if l.curselection():
        curpos = l.curselection()[0]
        if curpos > 0:
            l.selection_clear(curpos)
            l.selection_set(curpos-1)
            l.see(curpos-1)
        if curpos == 0:
            l.select_clear(curpos)
            l.selection_set(len(tmplist) - 1)
            l.see(len(tmplist) - 1)

def checkcb():
    global lastcbvalue
    global hookcbid
    if debug: print('checkcb')
    if pyperclip.paste().strip() != lastcbvalue:
        lastcbvalue = pyperclip.paste().strip()
        additem(lastcbvalue)
        lastcbvalue = ''
        pyperclip.copy('')
        if l.curselection():
            l.selection_clear(l.curselection()[0])   
        l.select_set("end")
        l.see("end")
    hookcbid = root.after(10, checkcb)

def savelisttofile():
    filename = tkinter.filedialog.asksaveasfile(initialdir=".")
    if filename:
        print(filename.name)
        filename.write('\n'.join(l.get(0,"end")))
        filename.close()
        #tkinter.messagebox.showinfo(
        #    title="File saved", 
        #    message=f"File `{filename.name}` has been saved to disk."
        #    )
    else:
        #tkinter.messagebox.showinfo(
        #    title="No filename received", 
        #    message=f"I did not receive a filename. Save failed."
        #    )
        print('No filename received.')

def togglekeyboardlistener():
    global listener
    if listener.running:
        listener.stop()
        togglekeyboard.set("Start keyboard listener")
    else:
        listener = pynput.keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
            win32_event_filter=win32_event_filter,
            darwin_intercept=darwin_intercept,
            #suppress=False,
            #uinput_device_paths=['/dev/input/event1'],
            )
        listener.start()  # start to listen on a separate thread
        togglekeyboard.set("Stop keyboard listener")

def removeblanklines():    
    if allowblankline.get():
        # blank lines are allowed, nothing to do, 
        # can't add back in blank lines
        pass
    else:
        tmpl = [x for x in l.get(0, 'end') if x]
        if tmpl == list(l.get(0, 'end')):
            # no need to remove blank lines or change my curpos
            pass
        else:                        
            clearclipboard()
            l.insert(0, *tmpl)
            l.selection_set(0)
            l.see(0)

def monitor_listener_thread():
    global keyforwardpressed
    global keyreversepressed
    if keyforwardpressed:
        keyforwardpressed = False
        typeline_goforward()
    elif keyreversepressed:
        keyreversepressed = False
        typeline_gobackward()
    else:
        # nothing
        pass
    root.after(50, monitor_listener_thread)
            

# Start of program
if __name__ == "__main__":
    # Define some variables
    debug = False
    # debug equal to True means listener is disabled 
    # The listener will run outside of the main thread
    # Use debug = True when running interactively (python3 -i)
    # use debug to test the GUI, not the keyboard listener
    #debug = True 

    # define the keylist as F1 through F12
    keylist = [f'f{n+1}' for n in range(12)]
    # keydict is only used in the win32_event_filter
    keydict = {
        key.name: key.value.vk for key in pynput.keyboard.Key 
        if key.name in keylist
            }
    keyforward = 'f3'
    keyreverse = 'f4'
    keyforwardpressed = False
    keyreversepressed = False
    lastcbvalue = ''
    hookcbid = ''
    test_clipboard = [f'sample text {x+1:02d}' for x in range(25)]

    # Start of tkinter GUI section
    root = tk.Tk()
    root.title('Paste List')
    root.minsize(666, 333)
    
    mygui = ttk.Frame(root, padding=(3,12,3,12))
    mygui.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    mygui.columnconfigure(5, weight=1)
    mygui.rowconfigure(15, weight=1)

    togglekeyboard = tk.StringVar(value="Stop keyboard listener")
    ttk.Button(
        mygui, textvariable=togglekeyboard, command=togglekeyboardlistener
        ).grid(
            column=1, row=1, sticky=tk.W
            )
    ttk.Label(
        mygui, text="Cycle Forward Key"
        ).grid(
            column=2, row=1, sticky=tk.E
            )
    forward = tk.StringVar()
    forward.set(keyforward)
    forwardcombo = ttk.Combobox(
        mygui, textvariable=forward, values=keylist, width=5
        )
    forwardcombo.grid(column=3, row=1, sticky=tk.W)

    forwardcombo.bind('<<ComboboxSelected>>', lambda e: updatefwkey())
    
    ttk.Label(
        mygui, text="Cycle Backward Key"
        ).grid(
            column=4, row=1, sticky=tk.E
            )
    backward = tk.StringVar()
    backward.set(keyreverse)
    backwardcombo = ttk.Combobox(
        mygui, textvariable=backward, values=keylist, width=5
        )
    backwardcombo.grid(column=5, row=1, sticky=tk.W)
    backwardcombo.bind('<<ComboboxSelected>>', lambda e: updatebwkey())

    clipboardlist = tk.StringVar(value=test_clipboard)
    l = tk.Listbox(mygui, height=15, listvariable=clipboardlist)
    l.grid(
        column=1, columnspan=5, row=2, rowspan=15, 
        sticky=(tk.N, tk.S, tk.E, tk.W)
        )
    l.selection_set(0)
    l.see(0)

    s = ttk.Scrollbar(mygui, orient=tk.VERTICAL, command=l.yview)
    s.grid(column=6, row=2, rowspan=20, sticky=(tk.N,tk.S))
    l['yscrollcommand'] = s.set

    hookcb = tk.BooleanVar()
    hookcb.set(False)
    hookit = ttk.Checkbutton(
        mygui, text="Hook Clipboard", variable=hookcb, 
        command=hookclipboard).grid(column=7, row=1, sticky=(tk.N,tk.W)
        )
    #if hookcb.get(): hookclipboard()

    allowblankline = tk.BooleanVar()
    allowblankline.set(False)
    hookit = ttk.Checkbutton(
        mygui, text="Allow blank lines", variable=allowblankline, 
        command=removeblanklines
        ).grid(
            column=7, row=2, sticky=(tk.N,tk.W)
            )
        
    ttk.Button(
        mygui, text="Remove item", command=removeitem
        ).grid(
            column=7, row=3, sticky=(tk.N, tk.W)
            )
    ttk.Button(
        mygui, text="Clear list", command=clearclipboard
        ).grid(
            column=7, row=4, sticky=(tk.N,tk.W)
            )
    ttk.Button(
        mygui, text="Import list from file", command=importcbfromfile
        ).grid(
            column=7, row=5, sticky=(tk.N,tk.W)
            )
    ttk.Button(
        mygui, text="Import list from file with vars", 
        command=importcbfromvarfile
        ).grid(
            column=7, row=6, sticky=(tk.N,tk.W)
            )
    ttk.Button(
        mygui, text="Save current list to file", command=savelisttofile
        ).grid(
            column=7, row=7, sticky=(tk.N,tk.W)
            )

    # main paste list box and scroll bar padding
    for child in mygui.winfo_children(): 
        child.grid_configure(padx=5, pady=5)
    l.grid_configure(padx=(5,0))
    s.grid_configure(padx=(0,5))

    controller = pynput.keyboard.Controller()
    listener = pynput.keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
        win32_event_filter=win32_event_filter,
        darwin_intercept=darwin_intercept,
        #suppress=False,
        #uinput_device_paths=['/dev/input/event1'],
        )
    if not debug: listener.start()  # start to listen on a separate thread
    if not debug: monitor_listener_thread()
    if not debug: root.mainloop()
    if not debug: listener.stop()
