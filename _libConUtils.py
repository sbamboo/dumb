# ConUtils: Console utility functions for python, Obs! xterm needed on linux 
# Made by: Simon Kalmi Claesson
# Version: 1.5

# [Imports]
import os
import platform
import time
import sys
import subprocess

# Console size (Curses)
def _setConSize_curses(width,height):
    '''Drawlib.conUtils: INTERNAL, gets the consoleSize using curses.'''
    try: import curses
    except:
        os.system(f"{sys.executable} -m pip install curses")
        import curses
    try:
        stdscr = curses.initscr()
        curses.resizeterm(height, width)
    finally:
        curses.endwin()

# Set console size
def setConSize(width,height):
    '''Drawlib.conUtils: Sets the console size on supported terminals (both inputs must be int)
    ConUtils is dependent on platform commands so this might not work everywere :/'''
    # Get platform
    platformv = platform.system()
    # Linux using resize
    if platformv == "Linux":
        os.system(f"resize -s {height} {width}")
    # Darwin using resize
    elif platformv == "Darwin":
        #os.system(f"resize -s {height} {width}")
        _setConSize_curses(width,height)
    # mode for windows
    elif platformv == "Windows":
        os.system(f'mode con: cols={width} lines={height}')
    # Error message if platform isn't supported
    else:
        raise Exception(f"Error: Platform {platformv} not supported yet!")

# Get console size
def getConSize_legacy() -> tuple:
    columns,rows = os.get_terminal_size()
    return columns,rows

# Set console title
def setConTitle(title):
    '''Drawlib.conUtils: Sets the console title on supported terminals (Input as string)
    ConUtils is dependent on platform commands so this might not work everywere :/'''
    # Get platform
    platformv = platform.system()
    # Linux using ANSI codes
    if platformv == "Linux":
        sys.stdout.write(f"\x1b]2;{title}\x07")
    # Mac not supported
    elif platformv == "Darwin":
        sys.stdout.write(f"\x1b]2;{title}\x07")
    # Windows using the title command
    elif platformv == "Windows":
        os.system(f'title {title}')
    # Error message if platform isn't supported
    else:
        raise Exception(f"Error: Platform {platformv} not supported yet!")

def callWithoutNl(inp=str):
    sys.stdout.flush()  # Flush stdout to make sure any pending output is written
    subprocess.call(inp, shell=True, stdout=subprocess.DEVNULL)

# Clear the screen
def clear(attemptNoNl=False,skipSetXY=False):
    '''Drawlib.conUtils: Attempts to clear the screen.
    ConUtils is dependent on platform commands so this might not work everywere :/'''
    # Get platform
    platformv = platform.system()
    # Linux using clear
    if platformv == "Linux":
        if attemptNoNl == True:
            callWithoutNl("clear")
        else:
            os.system("clear")
    # Mac using clear
    elif platformv == "Darwin":
        if attemptNoNl == True:
            callWithoutNl("clear")
        else:
            os.system(f"clear")
    # Windows using cls
    elif platformv == "Windows":
        if attemptNoNl == True:
            callWithoutNl("CLS")
        else:
            os.system("CLS")
    # Error message if platform isn't supported
    else:
        raise Exception(f"Error: Platform {platformv} not supported yet!")
    # SET x,y
    if skipSetXY != True: print("\033[0;0H",end="")

# Pause
def pause():
    '''Drawlib.conUtils: Pauses the terminal (Waits for input)
    ConUtils is dependent on platform commands so this might not work everywere :/'''
    # Get platform
    platformv = platform.system()
    # Linux using resize
    if platformv == "Linux":
        os.system(f"read -p ''")
    # Mac using resize
    elif platformv == "Darwin":
        os.system(f"read -n 1 -s -r -p ''")
    # Windows using PAUSE
    elif platformv == "Windows":
        os.system("PAUSE > nul")
    # Error message if platform isn't supported
    else:
        raise Exception(f"Error: Platform {platformv} not supported yet!")

# Debug boo function
def boo():
    '''Drawlib.conUtils: Smal testing function to execute a print statement.'''
    print("Boo! Oh now you are scared :)")

# Dummy function (call a dummy dummy to protect my yumme yummy tummy tummy)
def dummy():
    '''Drawlib.conUtils: Smal testing function that does nothing'''
    pass

# Os checker functions
def IsWindows() -> bool:
    '''Drawlib.conUtils: Checks if the platform name is Windows'''
    # Get platform and return boolean value depending of platform
    platformv = platform.system()
    if platformv == "Linux":
        return False
    elif platformv == "Darwin":
        return False
    elif platformv == "Windows":
        return True
    else:
        return False
def IsLinux() -> bool:
    '''Drawlib.conUtils: Checks if the platform name is Linux'''
    # Get platform and return boolean value depending of platform
    platformv = platform.system()
    if platformv == "Linux":
        return True
    elif platformv == "Darwin":
        return False
    elif platformv == "Windows":
        return False
    else:
        return False
def IsMacOS() -> bool:
    '''Drawlib.conUtils: Checks if the platform name is Darwin (Is Mac)'''
    # Get platform and return boolean value depending of platform
    platformv = platform.system()
    if platformv == "Linux":
        return False
    elif platformv == "Darwin":
        return True
    elif platformv == "Windows":
        return False
    else:
        return False

def GetPlatform() -> str:
    platformv = platform.system()
    plats = ["Linux","Darwin","Windows"]
    if platformv in plats:
        return platformv
    else:
        return None

def IsOs(platformName=str) -> bool:
    if platformName.lower() == "linux":
        return IsLinux()
    elif platformName.lower() == "darwin":
        return IsMacOS()
    elif platformName.lower() == "macos":
        return IsMacOS()
    elif platformName.lower() == "windows":
        return IsWindows()
    else:
        return False

def getConSize(cachePath=None,ask=True,defW=120,defH=30,_asker=input,_printer=print) -> tuple:
    "Gets consize and if unavaliable asks for config to cache."
    if cachePath == None:
        cachePath = os.getcwd()
    cacheType = "path"
    if type(cachePath) != str:
        cacheType = "stream"
    else:
        cachePath = os.path.join(cachePath,"conUtils_conSize.cache")
    w = None,
    h = None,
    try:
        w,h = os.get_terminal_size()
        valid = True
    except OSError:
        try:
            _ask = ask
            s = None
            if cacheType == "path":
                if os.path.exists(cachePath):
                    try: s = open(cachePath,'r').read()
                    except: pass
            else:
                s = cachePath.read()
            if s != None and "," in s:
                try:
                    w,h = s.strip().split(",")
                    w,h = int(w),int(h)
                    _ask = False
                except: pass
            if _ask == True:
                _printer("Couldn't get consize, want to set it? [<width:int>,<height:int>]")
                _printer(f"Will save to: {cachePath}")
                _printer(f"If not press enter to use defaults: {defW,defH}")
                inp = _asker("<w>,<h>: ")
                if inp.strip() == "":
                    w,h = defW,defH
                    valid = False
                else:
                    try:
                        w,h = [int(a.strip()) for a in inp.split(",")]
                        valid = True
                    except: pass
                try:
                    if cacheType == "path":
                        open(cachePath,'w').write(f"{w},{h}")
                    else:
                        cachePath.write(f"{w},{h}")
                except Exception as e:
                    _printer(f"Error while writing cache: {e}")
            else:
                if w == None or h == None:
                    valid = False
                else:
                    valid = True
        except Exception as e:
            valid = e
    except Exception as e:
        valid = e
    if valid == True:
        return (w,h)
    else:
        return (defW,defH)