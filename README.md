# Paste List

## Info

`Paste List` is a cross platform python program to use a dedicated key to paste from a list one line at a time.


## Features

- Cross platform compatible application (Windows, macOS, and Linux)
- Create a text list and paste the text line by line using a hotkey.
- Commands can be captured from the system clipboard or from a text file.
- There is an import option that allows vars in the file to be replaced with values from the user.
- The list will cycle back around to the top after the last command which makes it easy to paste a bunch of commands on a whole bunch of devices.
- This program was created to replace another software I was depending on but which has not been updated since 2010 or 2012: 
  - [ClipCycler](https://sourceforge.net/projects/clipcycler/).


## Installing and Running

Install [Python](python.org) if you do not already have python.

Download the `pastelist-<version>-<date>.pyw` from here. Also download the `requirements.txt` file. 

I would put the python file in a directory where I also plan on keeping my list files so that I don't have to navigate around much when using the import file option.

Launch the program. If it opens in IDLE, click `Run` > `Run Module`.

Test the program out. Open a text editor. Click the cycle forward and cycle backward keys (defaults are F3 and F4). If it types the text, it is working.

Create text file lists of things you would like to paste. Or use my vars file example below to create a text file and substitute those variables during import. You can save the file for later use too. Just remember the next time you will import it as just a plain text file, not one with vars.

If you want to add lines without using a text file, you can hook the clipboard. Then anything you copy is added to the paste list. Don't forget to unhook it, or you might be surprised more things are added to the list.


## Notes


### Windows

Just install Python from Python.org and install the required modules found in the requirements.txt file. 

Open cmd in the same folder and type `pip install -r requirements.txt`


### macOS

Recommended to download Python from Python.org and install it. Don't use the version of python that comes with macOS as it has issues with TCL/TK.

You'll also have to go into `Security & Privacy` > `Privacy` and add some applications to `Input Monitoring`, `Accessibility`, `Automation`, and/or `Developer Tools`. These applications might include `Terminal`, `IDLE.app`, `Python Launcher.app`, and `Python.app`.

I disabled `System Integrity Protection`, but I don't really think that is needed. 

You'll also need to install the required modules found in requirements.txt.


### Linux 

Tested on Ubuntu 22.04 (`$XDG_SESSION_TYPE=Wayland`). 

Linux is only working via Xorg at the moment which means you need to run under Xorg or use a program that uses XWayland. Also keyboard suppression is not currently implemented on Linux. You can modify this program to use keys which aren't on the keyboard such as F13 and F14 in place of F3 and F4. Then use xmodmap to map F3 and F4 to those keys. Or just find other F keys. 

You'll also need to install the required modules found in requirements.txt.


## Examples

### Example file with vars `<LANSW.vars.txt>`:

```
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
```
