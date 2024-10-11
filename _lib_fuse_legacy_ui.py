# Created with alpha.fusekit.lite 0.0.1 on 2024-09-22 22:58:53
# 

#fuse:imports
import os
#fuse:imports

def resolvePath(s,isdir:bool=False,tags:dict={}):
    if s.lstrip().startswith("./"):
        t = os.path.abspath(s.replace("./",parent+"/",1))
    elif s.lstrip().startswith(".\\"):
        t = os.path.abspath(s.replace(".\\",parent+"/",1).replace("\\","/"))
    else: t = s
    for tagk,tagv in tags.items():
        t = t.replace(tagk,tagv)
    if isdir == True:
        if not os.path.exists(t):
            os.makedirs(t)
    else:
        if not os.path.exists(os.path.dirname(t)):
            os.makedirs(os.path.dirname(t))
    return t

# Libraries
#region [fuse.include: ./libs/fancyPants.py]

import os
import requests
from bs4 import BeautifulSoup
from rich.progress import Progress as RichProgress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, DownloadColumn, RenderableColumn, TimeRemainingColumn, TransferSpeedColumn

def convert_bytes(bytes_size, binary_units=False):
    """Converts bytes to the highest prefix (B, kB, MB, GB, TB, PB or GiB, MiB, etc.)."""
    if binary_units:
        prefixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
        base = 1024
    else:
        prefixes = ['B', 'kB', 'MB', 'GB', 'TB', 'PB']
        base = 1000

    size = float(bytes_size)
    index = 0

    while size >= base and index < len(prefixes) - 1:
        size /= base
        index += 1

    return f"{size:.2f} {prefixes[index]}"


def get_optimal_block_size(file_size):
    """Determines an optimal block size based on file size."""
    if file_size < 1 * 1024 * 1024:  # < 1 MB
        return 8 * 1024  # 8 KB
    elif file_size < 100 * 1024 * 1024:  # < 100 MB
        return 64 * 1024  # 64 KB
    elif file_size < 1 * 1024 * 1024 * 1024:  # < 1 GB
        return 512 * 1024  # 512 KB
    elif file_size < 5 * 1024 * 1024 * 1024:  # < 5 GB
        return 1 * 1024 * 1024  # 1 MB
    
    #elif file_size < 10 * 1024 * 1024 * 1024:  # < 10 GB
    #    return 4 * 1024 * 1024  # 4 MB
    #elif file_size < 20 * 1024 * 1024 * 1024:  # < 20 GB
    #    return 8 * 1024 * 1024  # 8 MB
    #else:
    #    return 16 * 1024 * 1024  # 16 MB for very large files
    
    else:
        return 1 * 1024 * 1024  # 1 MB

def gdrive_vir_warn_url_extractor(HTMLsource):
    # attempt extract
    soup = BeautifulSoup(HTMLsource, 'html.parser')
    form = soup.find('form')
    linkBuild = form['action']
    hasParams = False
    inputs = form.find_all('input')
    toBeFound = ["id","export","confirm","uuid"]
    for inp in inputs:
        name = inp.attrs.get('name')
        value = inp.attrs.get('value')
        if name != None and name in toBeFound and value != None:
            if hasParams == False:
                pref = "?"
                hasParams = True
            else:
                pref = "&"
            linkBuild += f"{pref}{name}={value}"
    return linkBuild

class EventCancelSenser(Exception):
    def __init__(self, message):
        super().__init__(message)

class EventHandler:
    def __init__(self):
        self.children = {}
        self.event_id_counter = 0

    def _get_new_event_id(self):
        """Generates and returns a new unique event ID."""
        self.event_id_counter += 1
        return self.event_id_counter

    def create_generic(self, receiver, *args, **kwargs):
        """Creates a generic event receiver object and returns its event ID."""
        event_id = self._get_new_event_id()
        self.children[event_id] = receiver(self, *args, **kwargs)
        if not isinstance(self.children[event_id],EventReciever):
            raise TypeError("Newly created reciever was not of type and/or in inhertance of the 'EventReciever' object!")
        return event_id

    def get_reciever(self,event):
        return self.children[event]

    def update_progress(self, event, current_steps):
        """Updates the progress of a given event."""
        if event in self.children:
            self.children[event].update(current_steps)
    
    def update_params(self, event, **kwargs):
        """Updates the parameters of a given event."""
        if event in self.children:
            self.children[event].update_params(**kwargs)

    def reset_progress(self, event):
        """Resets the progress of a given event."""
        if event in self.children:
            self.children[event].reset()

    def end(self, event, successful=True):
        """Ends the progress of a given event and removes it from the handler."""
        if event in self.children:
            self.children[event].end(successful)
            del self.children[event]

class EventReciever:
    def __init__(self,parent):
        self.canceled = False
        if parent:
            self.parent = parent
        else:
            raise Exception("Parent must be sent when initing an EventReciever!")

    def update(self,current):
        raise NotImplementedError()

    def update_params(self,**kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)

    def reset(self):
        raise NotImplementedError()

    def end(self,successful):
        raise NotImplementedError()

class Progress(EventReciever):
    """Basic progress handler that prints '<current>/<total>'."""
    def __init__(self, parent, total_steps, block_size, conv_bytes=True, *un_used_a, **un_used_kw):
        super().__init__(parent)
        self.total_steps = total_steps
        self.current_steps = 0
        self.block_size = block_size
        self.conv_bytes = conv_bytes

    def update(self, current_steps):
        """Updates the progress and prints it."""
        self.current_steps = current_steps
        self.print_progress()

    def reset(self):
        self.current_steps = 0
        self.print_progress()

    def print_progress(self):
        """Prints the current progress in the format 'current/total'."""
        cur = self.current_steps
        tot = self.total_steps
        if self.conv_bytes == True:
            cur = convert_bytes(cur)
            tot = convert_bytes(tot)
        print(f'{cur}/{tot} (Block size: {convert_bytes(self.block_size)})')

    def end(self, successful):
        """Prints the status of the progress event as ended."""
        status = "Success" if successful else "Failed"
        print(f'Progress ended with status: {status}')

class ProgressRich(EventReciever):
    """Rich progress handler that uses a visual progress bar."""
    def __init__(self, parent, total_steps, block_size, title="Downloading...", conv_bytes=True, show_block_size=False, expand_task=False):
        super().__init__(parent)
        self.total_steps = total_steps
        self.current_steps = 0
        self.block_size = block_size  # Store block_size
        self.expand_task = expand_task
        self.title = title
        self.show_block_size = show_block_size

        # Include block size in the title if specified
        block_size_str = f" (bz: {convert_bytes(block_size)})" if show_block_size else ""
        self.progress = RichProgress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn() if conv_bytes == True else RenderableColumn(""),
            RenderableColumn("[cyan]ETA:"),
            TimeRemainingColumn(compact=True),
            TransferSpeedColumn(),
        )
        self.task = self.progress.add_task(title + block_size_str, total=total_steps)
        self.progress.start()  # Start the rich progress bar

    def update(self, current_steps):
        """Updates the rich progress bar."""
        self.current_steps = current_steps
        self.progress.update(self.task, completed=current_steps, expand=self.expand_task)

    def reset(self):
        self.current_steps = 0
        block_size_str = f" (bz: {convert_bytes(self.block_size)})" if self.show_block_size else ""
        self.progress.reset(self.task, expand=self.expand_task, total=self.total_steps, description=self.title+block_size_str)

    def end(self, successful):
        """Stops the rich progress bar and prints status."""
        self.progress.stop()  # Stop the rich progress bar

class ProgressTK(EventReciever):
    """Tkinter progress handler that displays a progress bar in a window."""
    def __init__(self, parent, total_steps, block_size, title="Download Progress", conv_bytes=True, onreset_text="Download reset. Ready to start again."):
        super().__init__(parent)

        import tkinter as tk
        from tkinter import ttk

        self.total_steps = total_steps
        self.current_steps = 0
        self.block_size = block_size
        self.conv_bytes = conv_bytes
        self.onreset_text = onreset_text

        # Create Tkinter window
        self.window = tk.Tk()
        self.window.title(title)
        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=20)
        
        self.label = tk.Label(self.window, text="Starting download...")
        self.label.pack(pady=10)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close
        self.window.geometry("400x100")
        
        self.window.update()

    def update(self, current_steps):
        """Updates the Tkinter progress bar."""
        if self.canceled == False:
            self.current_steps = current_steps
            self.progress_bar['value'] = (self.current_steps / self.total_steps) * 100
            cur = self.current_steps
            tot = self.total_steps
            if self.conv_bytes == True:
                cur = convert_bytes(cur)
                tot = convert_bytes(tot)
            self.label.config(text=f'Downloading: {cur}/{tot} ({(self.current_steps / self.total_steps) * 100:.2f}%) (Block size: {convert_bytes(self.block_size)})')
            self.window.update()

    def end(self, successful):
        """Closes the Tkinter window and prints status."""
        if self.canceled == False:
            self.window.destroy()  # Close the Tkinter window

    def on_close(self):
        """Handles window close event."""
        self.canceled = True # Tell ProgressTK and the downloader that this eventReciever is canceled
        self.window.destroy()  # Close the window

    def reset(self):
        """Resets the progress bar and current steps."""
        self.current_steps = 0
        self.progress_bar['value'] = 0
        self.label.config(text=self.onreset_text)
        self.window.update()


def downloadFile(url,output,stream=False, event_handler=EventHandler,progress_class=Progress, block_size="auto", force_steps=None, before_text=None,after_text=None, raise_for_status=True,on_file_exist_error="raise", progress_class_args=[], progress_class_kwargs={}, requests_args=[], requests_kwargs={}, text_printer=print, handle_gdrive_vir_warn=False,gdrive_vir_warn_text="Found gdrive scan warning, attempting to extract link and download from there...",gdrive_vir_warn_assumed_bytes=384,gdrive_new_stream=None, forced_encoding=None, _ovvEventId=None):
    """
    Function over requests.get that uses an EventHandler to allow for UI/TUI visual-progress of a file download.
    To just wrap requests.get and fetch content use `fetchUrl`.

    To not send events to a progress set both `event_handler` and `progress_class` to `None`.

    Parameters:
    -----------
    url            (str)          : The URL to download from.
    output         (str,stream)   : The filename/filepath/stream to output to. If filename instead of path, will use currentDictory. If stream set param `stream=True`.
    stream         (bool)         : If true the output is assumed to be a stream, and `open(...)` won't be called on the output.
    event_handler  (EventHandler) : INSTANCE, The event-handler to use. (Defaulted to `EventHandler`)
    progress_class (Progress)     : NOT-INSTANCE, The progress-class to send updates to. (Defaulted to `Progress`)
    block_size     (int,"auto")   : The block-size in bytes, or "auto" to determine based on total-file-size. (Defaulted to `"auto"`)
    force_steps    (int,None)     : Calculate and send events where progress is scaled into X amount of steps.
    before_text    (str,None)     : If not `None` will print this text to stdout before the download starts. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)
    after_text     (str,None)     : If not `None` will print this text to stdout after the download completes. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)

    raise_for_status    (bool)    : If set to `True` will raise when status_code is not `200`. (Defaulted to `True`)
    on_file_exist_error (str)     : How the function should behave when the file already exists. One of "raise"/"ignore"/"ignore-with-warn"/"remove"/"remove-with-warn". (Defaulted to `"raise"`)

    progress_class_args   (list)  : `*args` to send to the progress-class when event-handler inits it. (Defaulted to `[]`)
    progress_class_kwargs (dict)  : `*kwargs` to send to the progress-class when event-handler inits it. (Defaulted to `{}`)
    requests_args         (list)  : `*args` to send to the request.get method. (Defaulted to `[]`)
    requests_kwargs       (dict)  : `*kwargs` to send to the request.get method. (Defaulted to `{}`)

    text_printer    (callable)    : The function to call when printing before and after text, will be called with only the text as a param. (Defaulted to `print`)

    handle_gdrive_vir_warn       (bool) : If the function should try to indentify GoogleDrive-Virus-Warnings and try to get the download anyway. (Only enable if you trust the URL!)
    gdrive_vir_warn_text          (str) : The text to display when a warning is identified, set to `None` to disable.
    gdrive_vir_warn_assumed_bytes (int) : The amount of bytes the warning-identifier should look at for the '<!DOCTYPE html>' prefix. Must be more then `384` bytes!
    gdrive_new_stream          (stream) : If the output is a stream and we find a stream that can't be cleared using `.seek(0)` and `.truncate(0)` (dosen't have theese properties), this will be used to init a new stream instead.

    forced_encoding (str)         : Will tell requests to use this encoding, it will otherwise make a best attempt, same for GoogleDrive-Virus-Warnings. (Should be left at None unless you know the encoding and its a non-binary file)


    Returns:
    --------
    output (str,stream) : Returns the filepath (if filepath was given it returns using the currentDirectory) or stream that was written to.
    response            : If non `200` status code.

    Raises:
    -------
    *ExcFromRequests*: If error happends during download.
    Exception:         If enabled in params, when status is not `200`.
    IsADirectoryError: If output is not a stream and is a directory.


    Info:
    -----
    For what to place in 'progress_class_args' and 'progress_class_kwargs' see the classes deffinition. `total_size`, `block_size` and `conv_bytes` is sent by the function.
    It uses `EventHandler.create_generic(...)` and `EventHandler.update_progress(...)` aswell as `EventHandler.end(..., <success>)`. (See the `EventHandler` class)
    """
    
    # Check if we should not make a event sys
    if event_handler == None or progress_class == None:
        no_events = True
    else:
        no_events = False

    # Validate output
    if stream != True:
        # Is folder?
        if os.path.dirname(output) == True:
            raise IsADirectoryError(f"Output 'output' was a directory!")

        # Check if output is filename
        if os.path.isabs(output) or os.path.dirname(output) != '':
            # Just a filename, use current directory
            output = os.path.join(os.getcwd(), output)
        
        # File already exists?
        if os.path.exists(output):
            on_file_exist_error = on_file_exist_error.lower()
            if on_file_exist_error == "raise":
                raise FileExistsError(f"Failed to download the file: '{output}'! File already exists.")
            elif on_file_exist_error == "remove" or "-with-warn" in on_file_exist_error:
                if "-with-warn" in on_file_exist_error:
                    if "remove" in on_file_exist_error:
                        print(f"File '{output}' already exists, removing.")
                    else:
                        print(f"File '{output}' already exists, ignoring.")
                if "remove" in on_file_exist_error:
                    os.remove(output)

    # Create response object
    response = requests.get(url=url, stream=True, *requests_args, **requests_kwargs)
    if forced_encoding != None: response.encoding = forced_encoding
    total_size = int(response.headers.get('content-length', 0))

    # Forced steps?
    if force_steps == None:
        total_steps = total_size
    else:
        total_steps = force_steps

    # Determine block size if necessary
    o_block_size = block_size
    if block_size == "auto":
        block_size = get_optimal_block_size(total_size)

    # Initialize the progress bar if status Is_OK
    if response.status_code == 200:
        
        # Create a progress event based on the progressClass
        if no_events == False:
            if _ovvEventId != None:
                event_id = _ovvEventId
                event_handler.update_params(event_id, total_steps=total_steps, block_size=block_size)
                event_handler.reset_progress(event_id)
            else:
                event_id = event_handler.create_generic(progress_class, total_steps=total_steps, block_size=block_size, conv_bytes=(False if force_steps != None else True), *progress_class_args,**progress_class_kwargs)
        current_size = 0
        _event_obj_cached = None

        gdrive_vir_warn_first_bytes = b''
        gdrive_vir_warn_has_checked = False

        # Iterate over stream
        try:
            if before_text not in ["",None]: text_printer(before_text)

            # Stream?
            if stream == True:
                # Use the provided stream object directly
                for data in response.iter_content(block_size):
                    # Check for early-cancelation
                    if no_events == False:
                        if _event_obj_cached == None:
                            _event_obj_cached = event_handler.get_reciever(event_id)
                        if _event_obj_cached.canceled == True:
                            raise EventCancelSenser("event.receiver.cancelled")
                    # Check for empty
                    if not data:
                        break
                    # Check for gdrive-vir-warn, google url aswell as we not having checked the start yet
                    if handle_gdrive_vir_warn == True and "drive.google" in url and gdrive_vir_warn_has_checked == False:
                        # If block_size > byteAmnt or the currentlyTraversedContent is enough
                        if block_size >= gdrive_vir_warn_assumed_bytes or current_size >= gdrive_vir_warn_assumed_bytes:
                            attempted_decoded = None
                            # Attempt conversion
                            if forced_encoding != None:
                                attempted_encoding = forced_encoding
                            else:
                                attempted_encoding = response.apparent_encoding
                            # Default if none
                            if attempted_encoding == None: attempted_encoding = "utf-8"
                            # If we entered the condition based on block_size
                            if block_size > gdrive_vir_warn_assumed_bytes:
                                attempted_decoded = data.decode(attempted_encoding, errors='ignore')
                            # Otherwise check if we have buffered bytes
                            else:
                                if len(gdrive_vir_warn_first_bytes) >= gdrive_vir_warn_assumed_bytes:
                                    attempted_decoded = gdrive_vir_warn_first_bytes.decode(attempted_encoding, errors='ignore')
                            # Check content
                            if attempted_decoded != None:
                                gdrive_vir_warn_has_checked = True
                                if attempted_decoded.startswith('<!DOCTYPE html>') and "Google Drive - Virus scan warning" in attempted_decoded:
                                    newurl = gdrive_vir_warn_url_extractor(attempted_decoded)
                                    if type(newurl) == str and newurl.strip() != "":
                                        # Before starting a new download make a new stream object
                                        if hasattr(output, 'seek') and callable(getattr(output, 'seek')) and hasattr(output, 'truncate') and callable(getattr(output, 'truncate')):
                                            output.seek(0)       # Move to the start
                                            output.truncate(0)   # Clear the content
                                            newoutput_p = output
                                        else:
                                            if gdrive_new_stream == None:
                                                raise ValueError(f"Non clearable stream-output without 'gdrive_new_stream' being set! (Use an output stream with '.seek' and '.truncate' avaliable or set 'gdrive_new_stream')")
                                            else:
                                                newoutput_p = gdrive_new_stream
                                                # Close the old one?
                                                if hasattr(output, 'close') and callable(getattr(output, 'close')):
                                                    output.close()
                                        # Reset the progressbar
                                        if no_events == False:
                                            event_handler.reset_progress(event_id)
                                        # Begin a new download
                                        newoutput = downloadFile(
                                            newurl,
                                            newoutput_p,
                                            stream,
                                            event_handler,
                                            progress_class,
                                            o_block_size,
                                            force_steps,
                                            before_text,
                                            after_text,
                                            raise_for_status,
                                            on_file_exist_error,
                                            progress_class_args,
                                            progress_class_kwargs,
                                            requests_args,
                                            requests_kwargs,
                                            text_printer,
                                            handle_gdrive_vir_warn,
                                            gdrive_vir_warn_text,
                                            gdrive_vir_warn_assumed_bytes,
                                            None,
                                            forced_encoding,
                                            event_id if no_events == False else None
                                        )
                                        if isinstance(newoutput,response.__class__):
                                            raise Exception("Attempted download of gdrive-virus-warn extracted link returned a response instead of output, most likely failed by status-code!")
                                        # After text
                                        if after_text not in ["",None]: text_printer(after_text)
                                        # Close the progress and response
                                        response.close()
                                        if no_events == False:
                                            event_handler.end(event_id,successful=True)
                                        # Return
                                        return newoutput

                        # If fails meaning our block_size is to short or we haven't traversed enough add to the shortBuffer (max at 2x of gdrive_vir_warn_assumed_bytes)
                        else:
                            gdrive_vir_warn_first_bytes += data
                    # Progress
                    output.write(data)
                    if force_steps == None:
                        current_size += len(data)
                        if no_events == False:
                            event_handler.update_progress(event_id, current_size)
                    else:
                        current_size += len(data)
                        current_steps = int(round( (current_size/total_size) *total_steps ))
                        if no_events == False:
                            event_handler.update_progress(event_id, current_steps)

            # File
            else:
                # Open a file for writing
                with open(output, "wb") as f:
                    for data in response.iter_content(block_size):
                        # Check for early-cancelation
                        if no_events == False:
                            if _event_obj_cached == None:
                                _event_obj_cached = event_handler.get_reciever(event_id)
                            if _event_obj_cached.canceled == True:
                                raise EventCancelSenser("event.receiver.cancelled")
                        # Check for empty
                        if not data:
                            break
                        # Check for gdrive-vir-warn, google url aswell as we not having checked the start yet
                        if handle_gdrive_vir_warn == True and "drive.google" in url and gdrive_vir_warn_has_checked == False:
                            # If block_size > byteAmnt or the currentlyTraversedContent is enough
                            if block_size >= gdrive_vir_warn_assumed_bytes or current_size >= gdrive_vir_warn_assumed_bytes:
                                attempted_decoded = None
                                # Attempt conversion
                                if forced_encoding != None:
                                    attempted_encoding = forced_encoding
                                else:
                                    attempted_encoding = response.apparent_encoding
                                # Default if none
                                if attempted_encoding == None: attempted_encoding = "utf-8"
                                # If we entered the condition based on block_size
                                if block_size > gdrive_vir_warn_assumed_bytes:
                                    attempted_decoded = data.decode(attempted_encoding, errors='ignore')
                                # Otherwise check if we have buffered bytes
                                else:
                                    if len(gdrive_vir_warn_first_bytes) >= gdrive_vir_warn_assumed_bytes:
                                        attempted_decoded = gdrive_vir_warn_first_bytes.decode(attempted_encoding, errors='ignore')
                                # Check content
                                if attempted_decoded != None:
                                    gdrive_vir_warn_has_checked = True
                                    if attempted_decoded.startswith('<!DOCTYPE html>') and "Google Drive - Virus scan warning" in attempted_decoded:
                                        newurl = gdrive_vir_warn_url_extractor(attempted_decoded)
                                        if type(newurl) == str and newurl.strip() != "":
                                            # Before starting a new download make sure the output dosen't exist
                                            f.close()
                                            if os.path.exists(output):
                                                os.remove(output)
                                            # Reset the progressbar
                                            if no_events == False:
                                                event_handler.reset_progress(event_id)
                                            # Begin a new download
                                            newoutput = downloadFile(
                                                newurl,
                                                output,
                                                stream,
                                                event_handler,
                                                progress_class,
                                                o_block_size,
                                                force_steps,
                                                before_text,
                                                after_text,
                                                raise_for_status,
                                                on_file_exist_error,
                                                progress_class_args,
                                                progress_class_kwargs,
                                                requests_args,
                                                requests_kwargs,
                                                text_printer,
                                                handle_gdrive_vir_warn,
                                                gdrive_vir_warn_text,
                                                gdrive_vir_warn_assumed_bytes,
                                                None,
                                                forced_encoding,
                                                event_id if no_events == False else None
                                            )
                                            if isinstance(newoutput,response.__class__):
                                                raise Exception("Attempted download of gdrive-virus-warn extracted link returned a response instead of output, most likely failed by status-code!")
                                            # After text
                                            if after_text not in ["",None]: text_printer(after_text)
                                            # Close the progress and response
                                            response.close()
                                            if no_events == False:
                                                event_handler.end(event_id,successful=True)
                                            # Return
                                            return newoutput

                            # If fails meaning our block_size is to short or we haven't traversed enough add to the shortBuffer (max at 2x of gdrive_vir_warn_assumed_bytes)
                            else:
                                gdrive_vir_warn_first_bytes += data
                        # Progress
                        f.write(data)
                        if force_steps == None:
                            current_size += len(data)
                            if no_events == False:
                                event_handler.update_progress(event_id, current_size)
                        else:
                            current_size += len(data)
                            current_steps = int(round( (current_size/total_size) *total_steps ))
                            if no_events == False:
                                event_handler.update_progress(event_id, current_steps)
            
            # After text
            if after_text not in ["",None]: text_printer(after_text)

            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=True)

            # Return
            return output

        # Wops?
        except (KeyboardInterrupt, EventCancelSenser):
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
            if stream == False:
                if os.path.exists(output):
                    os.remove(output)
        except Exception as e:
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
            raise

    # Non 200 status_code
    else:
        if raise_for_status == True:
            if stream == True:
                raise Exception(f"Failed to download the file! Invalid status code ({response.status_code}).")
            else:
                raise Exception(f"Failed to download the file: '{output}'! Invalid status code ({response.status_code}).")
        else:
            return response

def fetchUrl(url, event_handler=EventHandler,progress_class=Progress, block_size="auto", force_steps=None, yield_response=False, before_text=None,after_text=None, raise_for_status=True, progress_class_args=[], progress_class_kwargs={}, requests_args=[], requests_kwargs={}, text_printer=print, handle_gdrive_vir_warn=False,gdrive_vir_warn_text="Found gdrive scan warning, attempting to extract link and download from there...",gdrive_vir_warn_assumed_bytes=384, forced_encoding=None, _ovvEventId=None):
    """
    Function over requests.get that uses an EventHandler to allow for UI/TUI visual-progress of a url-fetch.
    To just wrap requests.get and download to a file use `downloadFile`.

    To not send events to a progress set both `event_handler` and `progress_class` to `None`.

    Parameters:
    -----------
    url            (str)          : The URL to download from.
    event_handler  (EventHandler) : INSTANCE, The event-handler to use. (Defaulted to `EventHandler`)
    progress_class (Progress)     : NOT-INSTANCE, The progress-class to send updates to. (Defaulted to `Progress`)
    block_size     (int,"auto")   : The block-size in bytes, or "auto" to determine based on total-file-size. (Defaulted to `"auto"`)
    force_steps    (int,None)     : Calculate and send events where progress is scaled into X amount of steps.
    yield_response (bool)         : If `True` will return the response-object instead of `response.content`.
    before_text    (str,None)     : If not `None` will print this text to stdout before the download starts. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)
    after_text     (str,None)     : If not `None` will print this text to stdout after the download completes. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)

    raise_for_status    (bool)    : If set to `True` will raise when status_code is not `200`. (Defaulted to `True`)

    progress_class_args   (list)  : `*args` to send to the progress-class when event-handler inits it. (Defaulted to `[]`)
    progress_class_kwargs (dict)  : `*kwargs` to send to the progress-class when event-handler inits it. (Defaulted to `{}`)
    requests_args         (list)  : `*args` to send to the request.get method. (Defaulted to `[]`)
    requests_kwargs       (dict)  : `*kwargs` to send to the request.get method. (Defaulted to `{}`)

    text_printer    (callable)    : The function to call when printing before and after text, will be called with only the text as a param. (Defaulted to `print`)

    handle_gdrive_vir_warn       (bool) : If the function should try to indentify GoogleDrive-Virus-Warnings and try to get the download anyway. (Only enable if you trust the URL!)
    gdrive_vir_warn_text          (str) : The text to display when a warning is identified, set to `None` to disable.
    gdrive_vir_warn_assumed_bytes (int) : The amount of bytes the warning-identifier should look at for the '<!DOCTYPE html>' prefix. Must be more then `384` bytes!

    forced_encoding (str)         : Will tell requests to use this encoding, it will otherwise make a best attempt, same for GoogleDrive-Virus-Warnings. (Should be left at None unless you know the encoding and its a non-binary file)


    Returns:
    --------
    content  : If `yield_response` is `False`.
    response : If non `200` status code or `yield_response` is `True`.

    Raises:
    -------
    *ExcFromRequests*: If error happends during fetching.
    Exception:         If enabled in params, when status is not `200`.

    Info:
    -----
    For what to place in 'progress_class_args' and 'progress_class_kwargs' see the classes deffinition. `total_size`, `block_size` and `conv_bytes` is sent by the function.
    It uses `EventHandler.create_generic(...)` and `EventHandler.update_progress(...)` aswell as `EventHandler.end(..., <success>)`. (See the `EventHandler` class)
    """
    
    # Check if we should not make a event sys
    if event_handler == None or progress_class == None:
        no_events = True
    else:
        no_events = False

    # Create response object
    response = requests.get(url=url, stream=True, *requests_args, **requests_kwargs)
    if forced_encoding != None: response.encoding = forced_encoding
    total_size = int(response.headers.get('content-length', 0))

    # Forced steps?
    if force_steps == None:
        total_steps = total_size
    else:
        total_steps = force_steps

    # Determine block size if necessary
    o_block_size = block_size
    if block_size == "auto":
        block_size = get_optimal_block_size(total_size)

    # Initialize the progress bar if status Is_OK
    if response.status_code == 200:
        
        # Create a progress event based on the progressClass
        if no_events == False:
            if _ovvEventId != None:
                event_id = _ovvEventId
                event_handler.update_params(event_id, total_steps=total_steps, block_size=block_size)
                event_handler.reset_progress(event_id)
            else:
                event_id = event_handler.create_generic(progress_class, total_steps=total_steps, block_size=block_size, conv_bytes=(False if force_steps != None else True), *progress_class_args,**progress_class_kwargs)

        _event_obj_cached = None

        content_buffer = b''

        gdrive_vir_warn_has_checked = False

        # Iterate over stream
        try:
            if before_text not in ["",None]: text_printer(before_text)

            # Work
            for data in response.iter_content(block_size):
                # Check for early-cancelation
                if no_events == False:
                    if _event_obj_cached == None:
                        _event_obj_cached = event_handler.get_reciever(event_id)
                    if _event_obj_cached.canceled == True:
                        raise EventCancelSenser("event.receiver.cancelled")
                # Check for empty
                if not data:
                    break
                # Check for gdrive-vir-warn, google url aswell as we not having checked the start yet
                if handle_gdrive_vir_warn == True and "drive.google" in url and gdrive_vir_warn_has_checked == False:
                    # If block_size > byteAmnt or the currentlyTraversedContent is enough
                    if block_size >= gdrive_vir_warn_assumed_bytes or len(content_buffer) >= gdrive_vir_warn_assumed_bytes:
                        attempted_decoded = None
                        # Attempt conversion
                        if forced_encoding != None:
                            attempted_encoding = forced_encoding
                        else:
                            attempted_encoding = response.apparent_encoding
                        # Default if none
                        if attempted_encoding == None: attempted_encoding = "utf-8"
                        # If we entered the condition based on block_size
                        if block_size > gdrive_vir_warn_assumed_bytes:
                            attempted_decoded = data.decode(attempted_encoding, errors='ignore')
                        # Otherwise check if we have buffered bytes
                        else:
                            attempted_decoded = content_buffer.decode(attempted_encoding, errors='ignore')
                        # Check content
                        if attempted_decoded != None:
                            gdrive_vir_warn_has_checked = True
                            if attempted_decoded.startswith('<!DOCTYPE html>') and "Google Drive - Virus scan warning" in attempted_decoded:
                                newurl = gdrive_vir_warn_url_extractor(attempted_decoded)
                                if type(newurl) == str and newurl.strip() != "":
                                    # Before starting a new download empty the buffer
                                    #del content_buffer
                                    #content_buffer = b''
                                    # Reset the progressbar
                                    if no_events == False:
                                        event_handler.reset_progress(event_id)
                                    # Begin a new download
                                    newcontent = fetchUrl(
                                        newurl,
                                        event_handler,
                                        progress_class,
                                        o_block_size,
                                        force_steps,
                                        yield_response,
                                        before_text,
                                        after_text,
                                        raise_for_status,
                                        progress_class_args,
                                        progress_class_kwargs,
                                        requests_args,
                                        requests_kwargs,
                                        text_printer,
                                        handle_gdrive_vir_warn,
                                        gdrive_vir_warn_text,
                                        gdrive_vir_warn_assumed_bytes,
                                        forced_encoding,
                                        event_id if no_events == False else None
                                    )
                                    if isinstance(newcontent,response.__class__):
                                        raise Exception("Attempted download of gdrive-virus-warn extracted link returned a response instead of output, most likely failed by status-code!")
                                    # After text
                                    if after_text not in ["",None]: text_printer(after_text)
                                    # Close the progress and response
                                    response.close()
                                    if no_events == False:
                                        event_handler.end(event_id,successful=True)
                                    # Return
                                    return newcontent
                # Progress
                content_buffer += data
                if force_steps == None:
                    current_steps = int(round( (len(content_buffer)/total_size) *total_steps ))
                    if no_events == False:
                        handler.update_progress(event_id, current_steps)
                else:
                    if no_events == False:
                        handler.update_progress(event_id, len(content_buffer))
            
            # After Text
            if after_text not in ["",None]: text_printer(after_text)

            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=True)

            # Return
            if yield_response == True:
                # Return the response object with downloaded content
                response._content = content_buffer
                return response
            else:
                return content_buffer

        # Wops?
        except (KeyboardInterrupt, EventCancelSenser):
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
        except Exception as e:
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
            raise

    # Non 200 status_code
    else:
        if raise_for_status == True:
            raise Exception(f"Failed to fetch url, invalid status code ({response.status_code})!")
        else:
            return response
#endregion [fuse.include: ./libs/fancyPants.py]

# Code
#region [fuse.include: ./terminal.py]
#fuse:imports
import sys, os, subprocess, platform, json, ctypes, re
from dataclasses import dataclass

from typing import (
    Optional,
    Union,
    Mapping,
    TextIO,
    Callable,
    NamedTuple,
    Literal,
    Tuple,
    cast
)
from enum import IntEnum
#fuse:imports

STDOUT = -11 #Default Assumption

#region IMPORTA
class importa_v_1_2():
    def __init__(self):
        # Ensure importlib.util
        try:
            import importlib
            _ = getattr(importlib,"util")
        except AttributeError:
            from importlib import util as ua
            setattr(importlib,"util",ua)
            del ua
        self.importlib = importlib

    # Python
    def getExecutingPython(self) -> str:
        '''Returns the path to the python-executable used to start crosshell'''
        return sys.executable

    def _check_pip(self,pipOvw=None) -> bool:
        '''Checks if PIP is present'''
        if pipOvw != None and os.path.exists(pipOvw): pipPath = pipOvw
        else: pipPath = self.getExecutingPython()
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.check_call([pipPath, "-m", "pip", "--version"], stdout=devnull, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False
        return True

    def intpip(self,pip_args=str,pipOvw=None,pipMuteCommand=False,pipMuteEnsure=False):
        """Function to use pip from inside python, this function should also install pip if needed (Experimental)
        Returns: bool representing success or not
        
        NOTE! Might need --yes in args when using mute!"""

        if pipMuteCommand == True:
            subprocessParamsCommand = { "stdout":subprocess.DEVNULL, "stderr":subprocess.DEVNULL }
        else:
            subprocessParamsCommand = {}

        if pipMuteEnsure == True:
            subprocessParamsEnsure = { "stdout":subprocess.DEVNULL, "stderr":subprocess.DEVNULL }
        else:
            subprocessParamsEnsure = {}

        if pipOvw != None and os.path.exists(pipOvw): pipPath = pipOvw
        else: pipPath = self.getExecutingPython()
        if not self._check_pip(pipOvw):
            print("PIP not found. Installing pip...")
            get_pip_script = "https://bootstrap.pypa.io/get-pip.py"
            try:
                subprocess.check_call([pipPath, "-m", "ensurepip"],**subprocessParamsEnsure)
            except subprocess.CalledProcessError:
                print("Failed to install pip using ensurepip. Aborting.")
                return False
            try:
                subprocess.check_call([pipPath, "-m", "pip", "install", "--upgrade", "pip"],**subprocessParamsEnsure)
            except subprocess.CalledProcessError:
                print("Failed to upgrade pip. Aborting.")
                return False
            try:
                subprocess.check_call([pipPath, "-m", "pip", "install", get_pip_script],**subprocessParamsEnsure)
            except subprocess.CalledProcessError:
                print("Failed to install pip using get-pip.py. Aborting.")
                return False
            print("PIP installed successfully.")
        try:
            subprocess.check_call([pipPath, "-m", "pip"] + pip_args.split(),**subprocessParamsCommand)
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to execute pip command: {pip_args}")
            return False

    # Safe import function
    def autopipImport(self,moduleName=str,pipName=None,addPipArgsStr=None,cusPip=None,attr=None,relaunch=False,relaunchCmds=None,intpip_muteCommand=False,intpipt_mutePipEnsure=False):
        '''Tries to import the module, if failed installes using intpip and tries again.'''
        try:
            imported_module = self.importlib.import_module(moduleName)
        except:
            if pipName != None:
                command = f"install {pipName}"
            else:
                command = f"install {moduleName}"
            if addPipArgsStr != None:
                if not addPipArgsStr.startswith(" "):
                    addPipArgsStr = " " + addPipArgsStr
                command += addPipArgsStr
            if cusPip != None:
                #os.system(f"{cusPip} {command}")
                self.intpip(command,pipOvw=cusPip, pipMuteCommand=intpip_muteCommand,pipMuteEnsure=intpipt_mutePipEnsure)
            else:
                self.intpip(command, pipMuteCommand=intpip_muteCommand,pipMuteEnsure=intpipt_mutePipEnsure)
            if relaunch == True and relaunchCmds != None and "--noPipReload" not in relaunchCmds:
                relaunchCmds.append("--noPipReload")
                if "python" not in relaunchCmds[0] and self.isPythonRuntime(relaunchCmds[0]) == False:
                    relaunchCmds = [self.getExecutingPython(), *relaunchCmds]
                print("Relaunching to attempt reload of path...")
                print(f"With args:\n    {relaunchCmds}")
                subprocess.run([*relaunchCmds])
            else:
                imported_module = self.importlib.import_module(moduleName)
        if attr != None:
            return getattr(imported_module, attr)
        else:
            return imported_module

    # Function to load a module from path
    def fromPath(self,path, globals_dict=None):
        '''Import a module from a path. (Returns <module>)'''
        path = path.replace("/",os.sep).replace("\\",os.sep)
        spec = self.importlib.util.spec_from_file_location("module", path)
        module = self.importlib.util.module_from_spec(spec)
        if globals_dict:
            module.__dict__.update(globals_dict)
        spec.loader.exec_module(module)
        return module

    def fromPathAA(self,path, globals_dict=None):
        '''Import a module from a path, to be used as: globals().update(fromPathAA(<path>)) (Returns <module>.__dict__)'''
        path = path.replace("/",os.sep).replace("\\",os.sep)
        spec = self.importlib.util.spec_from_file_location("module", path)
        module = self.importlib.util.module_from_spec(spec)
        if globals_dict:
            module.__dict__.update(globals_dict)
        spec.loader.exec_module(module)
        return module.__dict__

    def installPipDeps(self,depsFile,encoding="utf-8",tagMapping=dict):
        '''Note! This takes a json file with a "deps" key, the fd function takes a deps list!'''
        deps = json.loads(open(depsFile,'r',encoding=encoding).read())["deps"]
        for dep in deps:
            for key,val in dep.items():
                for tag,tagVal in tagMapping.items():
                    dep[key] = val.replace("{"+tag+"}",tagVal)
                _ = self.autopipImport(**dep)
        
    def installPipDeps_fl(self,deps=list,tagMapping=dict):
        '''Note! This takes a deps list, the file function takes a json with a "deps" key!'''
        for dep in deps:
            for key,val in dep.items():
                for tag,tagVal in tagMapping.items():
                    dep[key] = val.replace("{"+tag+"}",tagVal)
                _ = self.autopipImport(**dep)
        
    def isPythonRuntime(self,filepath=str(),cusPip=None):
        exeFileEnds = [".exe"]
        if os.path.exists(filepath):
            try:
                # [Code]
                # Non Windows
                if platform.system() != "Windows":
                    try:
                        magic = self.importlib.import_module("magic")
                    except:
                        command = "install magic"
                        if cusPip != None:
                            #os.system(f"{cusPip} {command}")
                            self.intpip(command,pipOvw=cusPip)
                        else:
                            self.intpip(command)
                        magic = self.importlib.import_module("magic")
                    detected = magic.detect_from_filename(filepath)
                    return "application" in str(detected.mime_type)
                # Windows
                else:
                    fending = str("." +''.join(filepath.split('.')[-1]))
                    if fending in exeFileEnds:
                        return True
                    else:
                        return False
            except Exception as e: print("\033[31mAn error occurred!\033[0m",e)
        else:
            raise Exception(f"File not found: {filepath}")
#endregion IMPORTA

class OperationUnsupportedOnTerminal(Exception):
    def __init__(self, message="Attempted to call an operation on a terminal which dosen't support it!"):
        self.message = message
        super().__init__(self.message)

def _get_console_title_windows_cuzbuf():
    BUF_SIZE = 256
    buffer = ctypes.create_unicode_buffer(BUF_SIZE)
    ctypes.windll.kernel32.GetConsoleTitleW(buffer, BUF_SIZE)
    return buffer.value

def removeAnsiSequences(inputString):
    inputString = inputString.replace('',"\x1B")
    # Define a regular expression pattern to match ANSI escape sequences
    ansiPattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # Use re.sub to replace ANSI sequences with an empty string
    cleanedString = ansiPattern.sub('', inputString)
    return cleanedString

@dataclass
class WindowsConsoleFeatures_nonRichDependent:
    """
    From the rich library, its implementation here is to act as a part of a subset.
    """
    vt: bool = False
    truecolor: bool = False

class ColorSystem_nonRichDependent(): # super = IntEnum ?
    """
    This class is a value-lookup from the rich library,
    its implementation here is to act as a part of a subset.

    One of the 3 color system supported by terminals.
    """
    STANDARD = 1
    EIGHT_BIT = 2
    TRUECOLOR = 3
    WINDOWS = 4
    def __repr__(self) -> str:
        return f"ColorSystem.{self.name}"
    def __str__(self) -> str:
        return repr(self)

class ConsoleDimensions_nonRichDependent(): # super = NamedTuple ?
    """
    From the rich library, its implementation here is to act as a part of a subset.
    Size of the terminal.
    """
    width: int
    """The width of the console in 'cells'."""
    height: int
    """The height of the console in lines."""

class TerminalBaseClass():
    def __init__(self):
        self.propertiesHandlerId = "fuse_ui.terminalBase DONT-USE (2024-07-10)"

    def currenly_valid_colorsystem(self):
        return self.color_system in self.COLOR_SYSTEMS.values()

    def print_debug(self,skipComments:bool=False):
        if self.no_color == False and self.currenly_valid_colorsystem() == True and skipComments != True:
            self.parent.printer(f"""
    backend:          {self.propertiesHandlerId} \033[32m# The propertiesHandlerId (str)\033[0m
    platform:         {self.platform} \033[32m# Linux/Darwin/\033[9mJava\033[0m\033[32m/Windows (str)\033[0m
    is_jupyter:       {self.is_jupyter} \033[32m# If Jupyter-Notebook (bool)\033[0m
    is_interactive:   {self.is_interactive} \033[32m# False if ex. running a script. (bool)\033[0m
    is_terminal:      {self.is_terminal} \033[32m# If interactive and not dumb. (bool)\033[0m
    is_dumb_terminal: {self.is_dumb_terminal} \033[32m# If just I/O for net-term. (bool)\033[0m
    legacy_windows:   {self.legacy_windows} \033[32m# If running on LegacyWindows. (bool)\033[0m
    color_system:     {self.color_system.__repr__()} \033[32m# The current ColorSystem. (COLOR_SYSTEM:any)\033[0m
    ascii_only:       {self.ascii_only} \033[32m# If supports only ascii-charactters/sequences. (bool)\033[0m
    no_color:         {self.no_color} \033[32m# If color is unsupported or blocked. (bool)\033[0m
    encoding:         {self.encoding} \033[32m# The stdout encoding. (bool)\033[0m
    backend_size:     {self.backend_size} \033[32m# Size reported by backend. (bool)\033[0m

    windows_console_features:         {self.windows_console_features} \033[32m# (WindowsConsoleFeatures)\033[0m

    win32_avaliable:                  {self.win32_avaliable} \033[32m# Is the Win32-API avaliable. (bool)\033[0m
    win32_handle_value:               {self.win32_handle_value} \033[32m# The handle asked for. As defined in winbase.h. (bool)\033[0m
    win32_handle:                     {self.win32_handle} \033[32m# The handle-value returned by Win32-API. (bool)\033[0m
    win32_console_mode:               {self.win32_console_mode} \033[32m# Mode representation. https://docs.microsoft.com/en-us/windows/console/getconsolemode#parameters (DWORD/int)\033[0m
    win32_console_screen_buffer_info: {self.win32_console_screen_buffer_info} \033[32m# Information about the screen buffer. (dict)\033[0m
    win32_lwt_avaliable:              {self.win32_lwt_avaliable} \033[32m# Is the LegacyWindowsTerminal API avaliable. (bool)\033[0m
            """)
        else:
            self.parent.printer(f"""
    backend:          {self.propertiesHandlerId}
    platform:         {self.platform}
    is_jupyter:       {self.is_jupyter}
    is_interactive:   {self.is_interactive}
    is_terminal:      {self.is_terminal}
    is_dumb_terminal: {self.is_dumb_terminal}
    legacy_windows:   {self.legacy_windows}
    color_system:     {self.color_system.__repr__()}
    ascii_only:       {self.ascii_only}
    no_color:         {self.no_color}
    encoding:         {self.encoding}
    backend_size:     {self.backend_size}

    windows_console_features:         {self.windows_console_features}

    win32_avaliable:                  {self.win32_avaliable}
    win32_handle_value:               {self.win32_handle_value}
    win32_handle:                     {self.win32_handle}
    win32_console_mode:               {self.win32_console_mode}
    win32_console_screen_buffer_info: {self.win32_console_screen_buffer_info}
    win32_lwt_avaliable:              {self.win32_lwt_avaliable}
            """)

    @property
    def is_windows(self):
        return self.platform == "Windows"
    @property
    def is_macos(self):
        return self.platform == "Darwin"
    @property
    def is_darwin(self):
        return self.platform == "Darwin"
    @property
    def is_linux(self):
        return self.platform == "Windows"

    @property
    def output_mode(self) -> Literal["color-only","formatting-only","none","both"]:
        # self.is_terminal == False                           => No color+formatting
        # self.is_termianl == True, force_interactive == True => Color Only
        # self.is_dumb_terminal == True                       => No color+formatting
        # self.is_dumb_terminal == True, force_color == True  => Color Only
        # self.no_color == True                               => Formatting Only
        if self.is_dumb_terminal == True:
            if self.force_color == True:
                return "color-only"
            else:
                return "none"
        else:
            if self.is_terminal == False:
                if self.force_color == True:
                    return "color-only"
                else:
                    return "none"
            else:
                if self.force_interactive == False:
                    if self.no_color == True:
                        return "none"
                    else:
                        return "color-only"
                else:
                    if self.no_color == True:
                        return "formatting-only"
                    else:
                        return "both"
        

    #region EXPERIMENTAL
    def get_terminal_position(self,macOS_method=0, mutePipCommand=False, mutePipEnsure=False):

        if self.platform == 'Linux':
            try:
                import Xlib 
                from Xlib import display
            except:
                import os
                Xlib = self.importa_instance.autopipImport("Xlib","python-xlib", intpip_muteCommand=mutePipCommand,intpipt_mutePipEnsure=mutePipEnsure)
                try:
                    display = self.importa_instance.fromPath(os.path.join(os.path.dirname(Xlib.__file__),"display.py"))
                except ImportError:
                    display = getattr(Xlib,"display")
        
            try:
                d = display.Display()
                root = d.screen().root
                window_id = root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'), Xlib.X.AnyPropertyType).value[0]
                window = d.create_resource_object('window', window_id)
                geom = window.get_geometry()
                x, y = geom.x, geom.y

                # Considering window decorations (frame and title bar)
                geom = window.query_tree().parent.get_geometry()
                frame_x, frame_y = geom.x, geom.y
                return float(frame_x), float(frame_y)
            except Exception as e:
                print(f"Xlib method failed on Linux: {e}")

        elif self.platform == 'Darwin':
            # Implement method-0, applescript
            if macOS_method == 0:
                try:
                    script = '''
                    tell application "System Events"
                        set frontApp to name of first application process whose frontmost is true
                        tell process frontApp
                            set windowPos to position of front window
                        end tell
                    end tell
                    return windowPos
                    '''
                    position = subprocess.check_output(['osascript', '-e', script]).decode().strip()
                    x, y = map(int, position.split(', '))
                    return float(x), float(y)
                except Exception as e:
                    print(f"Could not determine position on MacOS: {e}")
                    
            # Implement method-1, helper application.
            elif macOS_method == 1:
                try:
                    import objc
                    from AppKit import NSApplication, NSWorkspace
                except ImportError:
                    objc = self.importa_instance.autopipImport("pyobjc",addPipArgsStr=" --user", intpip_muteCommand=mutePipCommand,intpipt_mutePipEnsure=mutePipEnsure)
                    try:
                        from AppKit import NSApplication, NSWorkspace
                    except:
                        AppKit = self.importa_instance.autopipImport("AppKit", intpip_muteCommand=mutePipCommand,intpipt_mutePipEnsure=mutePipEnsure)
                        NSApplication = AppKit.NSApplication
                        NSWorkspace = AppKit.NSWorkspace
                try:
                    app = NSWorkspace.sharedWorkspace().frontmostApplication()
                    #options = (objc.NSApplicationPresentationOptionHideDock |
                    #           objc.NSApplicationPresentationOptionHideMenuBar)
                    #NSApplication.sharedApplication().setPresentationOptions_(options)
                    NSApplication.sharedApplication()

                    app_name = app.localizedName()
                    script = f'''
                    tell application "System Events"
                        tell application "{app_name}" to get the bounds of the first window
                    end tell
                    '''
                    position = subprocess.check_output(['osascript', '-e', script]).decode().strip()
                    bounds = [int(n) for n in position.split(', ')]
                    x, y = bounds[0], bounds[1]
                    return float(x), float(y)
                except Exception as e:
                    print(f"Could not determine position on MacOS: {e}")
                    
            # Implement method 3
            elif macOS_method == 2:
                try:
                    objc = self.importa_instance.autopipImport("pyobjc",addPipArgsStr=" --user", intpip_muteCommand=mutePipCommand,intpipt_mutePipEnsure=mutePipEnsure)
                    from AppKit import NSWorkspace
                    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                except ImportError:
                    AppKit = self.importa_instance.autopipImport("AppKit", intpip_muteCommand=mutePipCommand,intpipt_mutePipEnsure=mutePipEnsure)
                    Quartz = self.importa_instance.autopipImport("Quartz", intpip_muteCommand=mutePipCommand,intpipt_mutePipEnsure=mutePipEnsure)
                    try:
                        from AppKit import NSWorkspace
                        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                    except:
                        NSWorkspace = AppKit.NSWorkspace
                        CGWindowListCopyWindowInfo = Quartz.CGWindowListCopyWindowInfo
                        kCGWindowListOptionOnScreenOnly = Quartz.kCGWindowListOptionOnScreenOnly
                        kCGNullWindowID = Quartz.kCGNullWindowID
                
                try:
                    # Get the active application
                    app = NSWorkspace.sharedWorkspace().frontmostApplication()
                    app_name = app.localizedName()

                    # Get list of windows
                    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                    for window in window_list:
                        if window['kCGWindowOwnerName'] == app_name:
                            bounds = window['kCGWindowBounds']
                            x = bounds['X']
                            y = bounds['Y']
                            return float(x), float(y)
                except Exception as e:
                    print(f"Could not determine position on MacOS: {e}")
            
            # Fallback
            else:
                print(f"Could not determine position on MacOS: Invalid macOS_method, int_0-2")

        elif self.platform == 'Windows':
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                x, y = rect.left, rect.top
                return float(x), float(y)
            except Exception as e:
                print(f"Could not determine position on Windows: {e}")

        return 0, 0
    #endregion EXPERIMENTAL

class TerminalProperties_nonRichDependent(TerminalBaseClass):
    """
    This class is a terminalProperties-handler that implements multiple functions.
    From the rich library, its implementation here is to act as a part of a subset.

    win32_handle: STDOUT=-11, STDERR=-12 #winbase.h
    """

    def __init__(
        self,

        parent:object,
        
        stdin:TextIO=sys.stdin,
        stdout:TextIO=sys.stdout,
        stderr:TextIO=sys.stderr,
        printer:Callable=print,

        color_system: Optional[Literal["auto", "standard", "256", "truecolor", "windows"]] = "auto",
        force_terminal:Optional[bool]=None,
        force_interactive:Optional[bool]=None,
        force_jupyter:Optional[bool]=None,
        legacy_windows:Optional[bool]=None,
        no_color: Optional[bool] = None,

        win32_handle:int = -11,

        _environ: Optional[Mapping[str, str]] = None,
        terminal_default_size = (80,25)
    ):

        super().__init__()

        self.propertiesHandlerId = "fuse_ui.NonRichDependent (2024-07-10)"

        #MARK: Make Instance
        self.importa_instance = importa_v_1_2()

        self.force_terminal = force_terminal
        self.force_interactive = force_interactive
        self.force_jupyter = force_jupyter
        self.force_legacy_windows = legacy_windows
        self.color_system_param = color_system
        self._environ = _environ if _environ != None else os.environ
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.terminal_default_size = terminal_default_size

        self.parent = parent
        self.encoding = (getattr(self.stdout, "encoding", "utf-8") or "utf-8").lower()
        self.platform:str = platform.system()
        self.windows_console_features = None
        self.color_system_raw:str = None
        self.is_interactive = (self.is_terminal and not self.is_dumb_terminal) if force_interactive is None else force_interactive
        self.ascii_only = not self.encoding.startswith("utf")
        self.no_color = no_color if no_color is not None else "NO_COLOR" in self._environ
        if "FORCE_COLOR" in self._environ:
            self.force_color = True
            self.no_color = False
        else:
            self.force_color = False

        self.win32_avaliable:bool = False
        self.win32_handle_value:int = win32_handle
        self.win32_handle:object = None
        self._win32_lwt = None
        self.win32_lwt_avaliable = False

        self.win32_binding_windll:object = None
        self.win32_binding_DWORD:object = None
        #self.win32_binding_COORD:object = None
        #self.win32_binding_WORD:object = None
        self.win32_binding_SMALL_RECT:object = None
        self.win32_binding_Structure:object = None
        self.win32_binding_byref:object = None
        self.win32_binding_CONSOLE_SCREEN_BUFFER_INFO = None
        self.win32_binding_BOOL:object = None
        self.win32_binding_HANDLE:object = None
        self.ctypes_binding_POINTER:object = None

        self._win32_console_mode:int = None

        self.get_windows_console_features()

        # Values from 'rich.console'
        self._TERM_COLORS = {
            "kitty": ColorSystem_nonRichDependent.EIGHT_BIT,
            "256color": ColorSystem_nonRichDependent.EIGHT_BIT,
            "16color": ColorSystem_nonRichDependent.STANDARD,
        }
        self.COLOR_SYSTEMS = {
            "standard": ColorSystem_nonRichDependent.STANDARD,
            "256": ColorSystem_nonRichDependent.EIGHT_BIT,
            "truecolor": ColorSystem_nonRichDependent.TRUECOLOR,
            "windows": ColorSystem_nonRichDependent.WINDOWS,
        }
        self._COLOR_SYSTEMS_NAMES = {system: name for name, system in self.COLOR_SYSTEMS.items()}

        # Defines from rich
        try:
           self._STDIN_FILENO = sys.__stdin__.fileno()
        except Exception:
            self._STDIN_FILENO = 0
        try:
            self._STDOUT_FILENO = sys.__stdout__.fileno()
        except Exception:
            self._STDOUT_FILENO = 1
        try:
            self._STDERR_FILENO = sys.__stderr__.fileno()
        except Exception:
            self._STDERR_FILENO = 2
        self._STD_STREAMS = (self._STDIN_FILENO, self._STDOUT_FILENO, self._STDERR_FILENO)
        self._STD_STREAMS_OUTPUT = (self._STDOUT_FILENO, self._STDERR_FILENO)

    def _get_windows_console_features(self) -> bool:
        # Var Defines
        fallback = WindowsConsoleFeatures_nonRichDependent()
        class LegacyWindowsError(Exception): pass
        # Check so we are on windows
        if sys.platform != "win32":
            return fallback
        else:
            # Check so windll is avaliable
            try:
                from ctypes import WinDLL, LibraryLoader, Structure, byref, POINTER
                from ctypes.wintypes import DWORD,HANDLE,_SMALL_RECT,SMALL_RECT,_COORD,WORD,LPDWORD,BOOL
                self.win32_binding_HANDLE = HANDLE
                self.win32_binding_DWORD = DWORD
                #self.win32_binding_COORD = COORD
                #self.win32_binding_WORD = WORD
                self.win32_binding_windll = LibraryLoader(WinDLL)
                self.win32_binding_SMALL_RECT = _SMALL_RECT
                self.win32_binding_Structure = Structure
                self.win32_binding_byref = byref
                self.ctypes_binding_POINTER = POINTER
                self.win32_binding_BOOL = BOOL
                class CONSOLE_SCREEN_BUFFER_INFO(Structure):
                    _fields_ = [
                        ("dwSize", _COORD),
                        ("dwCursorPosition", _COORD),
                        ("wAttributes", WORD),
                        ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", _COORD),
                    ]
                self.win32_binding_CONSOLE_SCREEN_BUFFER_INFO = CONSOLE_SCREEN_BUFFER_INFO
            except (AttributeError,ImportError,ValueError):
                return fallback
            self.win32_avaliable = True
            # GetStdHandle
            _GetStdHandle = self.win32_binding_windll.kernel32.GetStdHandle
            _GetStdHandle.argtypes = [
                DWORD,
            ]
            _GetStdHandle.restype = HANDLE
            self.win32_handle = cast(HANDLE, _GetStdHandle(self.win32_handle_value))
            # Check Features
            try:
                # GetConsoleMode
                console_mode = DWORD()
                _GetConsoleMode = self.win32_binding_windll.kernel32.GetConsoleMode
                _GetConsoleMode.argtypes = [HANDLE, LPDWORD]
                _GetConsoleMode.restype = BOOL
                success = bool(_GetConsoleMode(self.win32_handle, console_mode))
                if not success:
                    raise LegacyWindowsError("Unable to get legacy Windows Console Mode")
                console_mode_value = console_mode.value
                self._win32_console_mode = console_mode_value
                success = True
            except LegacyWindowsError:
                console_mode_value = 0
                success = False
            # Calculate 'vt' feature
            vt = bool(success and console_mode_value & 4) #ENABLE_VIRTUAL_TERMINAL_PROCESSING = 4
            # Calculate 'truecolor' feature
            truecolor = False
            if vt:
                win_version = sys.getwindowsversion()
                truecolor = win_version.major > 10 or (
                    win_version.major == 10 and win_version.build >= 15063
                )
            # Return
            return WindowsConsoleFeatures_nonRichDependent(vt=vt, truecolor=truecolor)

    def get_windows_console_features(self) -> "WindowsConsoleFeatures_nonRichDependent":
        if self.windows_console_features is None:
            self.windows_console_features = self._get_windows_console_features()
        return self.windows_console_features

    @property
    def is_jupyter(self) -> bool:
        """Check if we're running in a Jupyter notebook."""
        if self.force_jupyter != None:
            return self.force_jupyter
        try:
            get_ipython  # type: ignore[name-defined]
        except NameError:
            return False
        ipython = get_ipython()  # type: ignore[name-defined]
        shell = ipython.__class__.__name__
        if (
            "google.colab" in str(ipython.__class__)
            or os.getenv("DATABRICKS_RUNTIME_VERSION")
            or shell == "ZMQInteractiveShell"
        ):
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)

    @property
    def legacy_windows(self) -> bool:
        if self.force_legacy_windows != None:
            return self.force_legacy_windows
        return (self.platform == "Windows" and not self.get_windows_console_features().vt) and not self.is_jupyter

    @property
    def is_terminal(self) -> bool:
        if self.force_terminal != None:
            return self.force_terminal
        if hasattr(sys.stdin, "__module__") and sys.stdin.__module__.startswith(
                "idlelib"
            ):
            # Return False for Idle which claims to be a tty but can't handle ansi codes
            return False
        if self.is_jupyter:
            # return False for Jupyter, which may have FORCE_COLOR set
            return False

        # If FORCE_COLOR env var has any value at all, we assume a terminal.
        force_color = self._environ.get("FORCE_COLOR")
        if force_color is not None:
            return True
        
        isatty: Optional[Callable[[], bool]] = getattr(sys.stdout, "isatty", None)
        try:
            return False if isatty is None else isatty()
        except ValueError:
            # in some situation (at the end of a pytest run for example) isatty() can raise
            # ValueError: I/O operation on closed file
            # return False because we aren't in a terminal anymore
            return False

    @property
    def is_dumb_terminal(self) -> bool:
        _term = self._environ.get("TERM", "")
        is_dumb = _term.lower() in ("dumb", "unknown")
        return self.is_terminal and is_dumb

    def _color_system(self) -> Optional[ColorSystem_nonRichDependent]:
        if self.is_jupyter:
            return ColorSystem_nonRichDependent.TRUECOLOR
        if not self.is_terminal or self.is_dumb_terminal:
            return None
        if self.platform == "Windows":
            if self.legacy_windows:
                return ColorSystem_nonRichDependent.WINDOWS
            windows_console_features = self.get_windows_console_features()
            return (
                ColorSystem_nonRichDependent.TRUECOLOR
                if windows_console_features.truecolor
                else ColorSystem_nonRichDependent.EIGHT_BIT
            )
        else:
            color_term = self._environ.get("COLORTERM", "").strip().lower()
            if color_term in ("truecolor", "24bit"):
                return ColorSystem_nonRichDependent.TRUECOLOR
            term = self._environ.get("TERM", "").strip().lower()
            _term_name, _hyphen, colors = term.rpartition("-")
            color_system = self._TERM_COLORS.get(colors, ColorSystem_nonRichDependent.STANDARD)
            return color_system

    @property
    def color_system(self) -> Optional[ColorSystem_nonRichDependent]:
        if self.color_system_param == "auto":
            color_system = self._color_system()
        else:
            color_system = self.COLOR_SYSTEMS[self.color_system_param]
        self.color_system_raw = self._COLOR_SYSTEMS_NAMES[color_system]
        return color_system

    @property
    def backend_size(self) -> "ConsoleDimensions_nonRichDependent":
        if self.is_dumb_terminal:
            return ConsoleDimensions_nonRichDependent(*self.terminal_default_size)
        
        width: Optional[int] = None
        height: Optional[int] = None

        if self.platform == "Windows":
            try:
                    width, height = os.get_terminal_size()
            except (AttributeError, ValueError, OSError):  # Probably not a terminal
                pass
        else:
            for file_descriptor in self._STD_STREAMS:
                try:
                    width, height = os.get_terminal_size(file_descriptor)
                except (AttributeError, ValueError, OSError):
                    pass
                else:
                    break

        columns = self._environ.get("COLUMNS")
        if columns is not None and columns.isdigit():
            width = int(columns)
        lines = self._environ.get("LINES")
        if lines is not None and lines.isdigit():
            height = int(lines)

        # get_terminal_size can report 0, 0 if run from pseudo-terminal
        width = width or self.terminal_default_size[0]
        height = height or self.terminal_default_size[1]
        return ConsoleDimensions_nonRichDependent(
            width - self.legacy_windows,
            height,
        )

    @property
    def win32_console_mode(self) -> Union[int,None]:
        """Int value representing the current console mode as documented at:
        https://docs.microsoft.com/en-us/windows/console/getconsolemode#parameters"""
        if self.win32_avaliable == True:
            # GetConsoleMode
            console_mode = self.win32_binding_DWORD()
            success = bool(self.win32_binding_windll.kernel32.GetConsoleMode(self.win32_handle, console_mode))
            if not success:
                class LegacyWindowsError(Exception): pass
                raise LegacyWindowsError("Unable to get legacy Windows Console Mode")
            console_mode_value = console_mode.value
            self._win32_console_mode = console_mode_value
            return console_mode_value
        else:
            return self._win32_console_mode

    @property
    def win32_console_screen_buffer_info_obj(self):
        console_screen_buffer_info = self.win32_binding_CONSOLE_SCREEN_BUFFER_INFO()
        _GetConsoleScreenBufferInfo =  self.win32_binding_windll.kernel32.GetConsoleScreenBufferInfo
        _GetConsoleScreenBufferInfo.argtypes = [
            self.win32_binding_HANDLE,
            self.ctypes_binding_POINTER(self.win32_binding_CONSOLE_SCREEN_BUFFER_INFO),
        ]
        _GetConsoleScreenBufferInfo.restype = self.win32_binding_BOOL
        _GetConsoleScreenBufferInfo(self.win32_handle, self.win32_binding_byref(console_screen_buffer_info))
        return console_screen_buffer_info
    
    @property
    def win32_console_screen_buffer_info(self):
        if self.win32_avaliable == True:
            class sRect_stripped(self.win32_binding_SMALL_RECT):
                def castor(self,obj):
                    self.Left = obj.Left
                    self.Top = obj.Top
                    self.Right = obj.Right
                    self.Bottom = obj.Bottom
                    return self
                def __repr__(self) -> str:
                    return f"_SMALL_RECT-stripped(Left:{self.Left},Top:{self.Top},Right:{self.Right},Bottom:{self.Bottom})"
            # Get console screen buffer info
            return {
                "dwSize": (self.win32_console_screen_buffer_info_obj.dwSize.X,self.win32_console_screen_buffer_info_obj.dwSize.Y),
                "dwCursorPosition": (self.win32_console_screen_buffer_info_obj.dwCursorPosition.X,self.win32_console_screen_buffer_info_obj.dwCursorPosition.Y),
                "wAttributes": self.win32_console_screen_buffer_info_obj.wAttributes,
                "srWindow": sRect_stripped().castor(self.win32_console_screen_buffer_info_obj.srWindow),
                "dwMaximumWindowSize": (self.win32_console_screen_buffer_info_obj.dwMaximumWindowSize.X,self.win32_console_screen_buffer_info_obj.dwMaximumWindowSize.Y)
            }
        else:
            class sRect_stripped():
                def __init__(self):
                    self.Left = None
                    self.Top = None
                    self.Right = None
                    self.Bottom = None
                def castor(self,obj):
                    self.Left = obj.Left
                    self.Top = obj.Top
                    self.Right = obj.Right
                    self.Bottom = obj.Bottom
                    return self
                def __repr__(self) -> str:
                    return f"_SMALL_RECT-stripped(Left:{self.Left},Top:{self.Top},Right:{self.Right},Bottom:{self.Bottom})"
            return {
                "dwSize": (None,None),
                "dwCursorPosition": (None,None),
                "wAttributes": int(),
                "srWindow": sRect_stripped(),
                "dwMaximumWindowSize": (None,None)
            }

class TerminalProperties_richDependent(TerminalBaseClass):
    """
    win32_handle: STDOUT=-11, STDERR=-12 #winbase.h
    """

    def __init__(
        self,

        parent:object,
        
        stdin:TextIO=sys.stdin,
        stdout:TextIO=sys.stdout,
        stderr:TextIO=sys.stderr,
        printer:Callable=print,

        autoGetRich:bool = False,
        couple_rich_stdout:bool = False,

        color_system: Optional[Literal["auto", "standard", "256", "truecolor", "windows"]] = "auto",
        force_terminal:Optional[bool]=None,
        force_interactive:Optional[bool]=None,
        force_jupyter:Optional[bool]=None,
        legacy_windows:Optional[bool]=None,
        no_color: Optional[bool] = None,
        rich_emoji: bool = True,
        rich_emoji_variant: Optional[Literal["emoji", "text"]] = None,

        win32_handle:int = -11,

        _environ: Optional[Mapping[str, str]] = None,
        terminal_default_size = (80,25)
    ):

        super().__init__()

        self.propertiesHandlerId = "fuse_ui.RichDependent (2024-07-10)"

        #MARK: Make Instance
        self.importa_instance = importa_v_1_2()

        self.force_terminal = force_terminal
        self.force_interactive = force_interactive
        self.force_jupyter = force_jupyter
        self.force_legacy_windows = legacy_windows
        self.color_system_param = color_system
        self._environ = _environ if _environ != None else os.environ
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.terminal_default_size = terminal_default_size

        self.parent = parent
        self.platform:str = platform.system()
        self.windows_console_features = None
        self.color_system_raw:str = None

        self.win32_avaliable:bool = False
        self.win32_handle_value:int = win32_handle
        self.win32_handle:object = None

        self.win32_binding_SMALL_RECT:object = None

        # Imports
        try:
            from rich.console import Console, get_windows_console_features
            from rich.console import COLOR_SYSTEMS as rich_COLOR_SYSTEMS
            from rich.control import CONTROL_CODES_FORMAT as rich_CONTROL_CODES_FORMAT
            from rich.segment import ControlType as rich_ControlType
            from rich.control import Control as rich_Control

            try:
                from rich._win32_console import (
                    GetConsoleMode,
                    GetStdHandle,
                    WindowsCoordinates,
                    LegacyWindowsTerm,
                    GetConsoleScreenBufferInfo,
                    COORD
                )
                from ctypes import wintypes
                self.win32_binding_SMALL_RECT = wintypes._SMALL_RECT
                self.win32_avaliable = True
            except:
                self.win32_avaliable = False
        except:
            if autoGetRich == True:
                _rich = self.importa_instance.autopipImport("rich")
                _rich = self.importa_instance.autopipImport("rich")
                _parent = os.path.dirname(_rich.__file__)
                # console
                _file = os.path.join(_parent,"console.py")
                _console = self.importa_instance.fromPath( _file )
                # control
                _file = os.path.join(_parent,"control.py")
                _control = self.importa_instance.fromPath( _file )
                # segment
                _file = os.path.join(_parent,"segment.py")
                _segment = self.importa_instance.fromPath( _file )
                # Imports
                Console = _console.Console
                get_windows_console_features = _console.get_windows_console_features
                rich_CONTROL_CODES_FORMAT = _control.CONTROL_CODES_FORMAT
                rich_COLOR_SYSTEMS = _console.COLOR_SYSTEMS
                rich_Control = _control.ControlType
                rich_ControlType = _segment.ControlType
                try:
                    # _win32_console
                    _file = os.path.join(_parent,"_win32_console.py")
                    if os.path.exists(_file):
                        _win32_console = self.importa_instance.fromPath( _file )
                        _l = ["GetConsoleMode", "GetStdHandle", "WindowsCoordinates", "LegacyWindowsTerm", "GetConsoleScreenBufferInfo", "COORD"]
                        for prop in _l:
                            setattr(self,prop,getattr(_win32_console,prop))
                        self.win32_avaliable = True
                    else:
                        self.win32_avaliable = False    
                except:
                    self.win32_avaliable = False
            else:
                raise

        # Mappings
        if self.win32_avaliable == True and autoGetRich == False:
            self.GetConsoleMode = GetConsoleMode
            self.GetConsoleScreenBufferInfo = GetConsoleScreenBufferInfo
            self.get_windows_console_features = get_windows_console_features
            self.Console = Console
            self.rich_CONTROL_CODES_FORMAT = rich_CONTROL_CODES_FORMAT
            self.wintypes = wintypes
            self.rich_ControlType = rich_ControlType
            self.GetStdHandle = GetStdHandle
            self.WindowsCoordinates = WindowsCoordinates
            self.LegacyWindowsTerm = LegacyWindowsTerm

        self.initated_params = {
            "no_color": no_color,
            "rich_emoji": rich_emoji,
            "rich_emoji_variant": rich_emoji_variant
        }

        # Instancing
        self.ada = {
            "stderr": self.stderr
        }
        if couple_rich_stdout == True:
            self.ada["file"] = self.stdout

        self.rich_console_instance = self.Console(
            **self.ada,
            color_system= self.color_system_param,
            force_terminal= self.force_terminal,
            force_jupyter= self.force_jupyter,
            force_interactive= self.force_interactive,
            no_color= no_color,
            emoji= rich_emoji,
            emoji_variant= rich_emoji_variant,
            legacy_windows= self.force_legacy_windows
        )

        # Properties
        self.is_jupyter = self.rich_console_instance.is_jupyter
        self.is_interactive = self.rich_console_instance.is_interactive
        self.is_terminal = self.rich_console_instance.is_terminal
        self.is_dumb_terminal = self.rich_console_instance.is_dumb_terminal
        self.legacy_windows = self.rich_console_instance.legacy_windows
        self.color_system = self.rich_console_instance._color_system
        self.color_system_raw = self.rich_console_instance.color_system
        self.ascii_only = self.rich_console_instance.options.ascii_only
        self.windows_console_features = get_windows_console_features()
        self.encoding = self.rich_console_instance.encoding
        self.backend_size = self.rich_console_instance.size
        self.no_color = self.rich_console_instance.no_color
        if "FORCE_COLOR" in self._environ:
            self.force_color = True
            self.no_color = False
        else:
            self.force_color = False

        self.COLOR_SYSTEMS = rich_COLOR_SYSTEMS
        
        # Win32
        if self.win32_avaliable == True:
            self.win32_handle = self.GetStdHandle(self.win32_handle_value)
            self._win32_lwt = self.LegacyWindowsTerm(self.stdout)
            self.win32_lwt_avaliable = True
        else:
            self._win32_lwt = None
            self.win32_lwt_avaliable = False

    @property
    def win32_console_mode(self) -> Union[int,None]:
        """Int value representing the current console mode as documented at:
        https://docs.microsoft.com/en-us/windows/console/getconsolemode#parameters"""
        if self.win32_avaliable == True:
            return self.GetConsoleMode(self.win32_handle)
        else:
            return None

    @property
    def win32_console_screen_buffer_info(self):
        if self.win32_avaliable == True:
            class sRect_stripped(self.win32_binding_SMALL_RECT):
                def castor(self,obj):
                    self.Left = obj.Left
                    self.Top = obj.Top
                    self.Right = obj.Right
                    self.Bottom = obj.Bottom
                    return self
                def __repr__(self) -> str:
                    return f"_SMALL_RECT-stripped(Left:{self.Left},Top:{self.Top},Right:{self.Right},Bottom:{self.Bottom})"
            _win32_console_screen_buffer_info = self.GetConsoleScreenBufferInfo(self.win32_handle)
            return {
                "dwSize": (_win32_console_screen_buffer_info.dwSize.X,_win32_console_screen_buffer_info.dwSize.Y),
                "dwCursorPosition": (_win32_console_screen_buffer_info.dwCursorPosition.X,_win32_console_screen_buffer_info.dwCursorPosition.Y),
                "wAttributes": _win32_console_screen_buffer_info.wAttributes,
                "srWindow": sRect_stripped().castor(_win32_console_screen_buffer_info.srWindow),
                "dwMaximumWindowSize": (_win32_console_screen_buffer_info.dwMaximumWindowSize.X,_win32_console_screen_buffer_info.dwMaximumWindowSize.Y)
            }
        else:
            class sRect_stripped():
                def __init__(self):
                    self.Left = None
                    self.Top = None
                    self.Right = None
                    self.Bottom = None
                def castor(self,obj):
                    self.Left = obj.Left
                    self.Top = obj.Top
                    self.Right = obj.Right
                    self.Bottom = obj.Bottom
                    return self
                def __repr__(self) -> str:
                    return f"_SMALL_RECT-stripped(Left:{self.Left},Top:{self.Top},Right:{self.Right},Bottom:{self.Bottom})"
            return {
                "dwSize": (None,None),
                "dwCursorPosition": (None,None),
                "wAttributes": int(),
                "srWindow": sRect_stripped(),
                "dwMaximumWindowSize": (None,None)
            }

    @property
    def win32_console_screen_buffer_info_obj(self):
        return self.GetConsoleScreenBufferInfo(self.win32_handle)

    def update_backend(self):
        self.rich_console_instance = self.Console(
            **self.ada,
            color_system= self.color_system_param,
            force_terminal= self.force_terminal,
            force_jupyter= self.force_jupyter,
            force_interactive= self.force_interactive,
            no_color= self.initiated_params["no_color"],
            emoji= self.initated_params["rich_emoji"],
            emoji_variant= self.initated_params["rich_emoji_variant"],
            legacy_windows= self.force_legacy_windows
        )

        # Properties
        self.is_jupyter = self.rich_console_instance.is_jupyter
        self.is_interactive = self.rich_console_instance.is_interactive
        self.is_terminal = self.rich_console_instance.is_terminal
        self.is_dumb_terminal = self.rich_console_instance.is_dumb_terminal
        self.legacy_windows = self.rich_console_instance.legacy_windows
        self.color_system = self.rich_console_instance._color_system
        self.color_system_raw = self.rich_console_instance.color_system
        self.ascii_only = self.rich_console_instance.options.ascii_only
        self.windows_console_features = self.get_windows_console_features()
        self.encoding = self.rich_console_instance.encoding
        self.backend_size = self.rich_console_instance.size
        self.no_color = self.rich_console_instance.no_color

    def rich_control(self,code,*param):
        """Call rich control code and get its ANSI/text equivalent."""
        if not self.is_dumb_terminal:
            return self.rich_CONTROL_CODES_FORMAT[code](*param)

#endregion [fuse.include: ./terminal.py]
#region [fuse.include: ./formatting.py]

#fuse:imports
import math, re
from typing import Union, Tuple, Literal
#fuse:imports

class InvalidCommonOrNativeFormat(Exception):
    def __init__(self, message:str="Attempted to call an operation with an invalid input!",context:str=None):
        self.message = message
        if context not in ["",None]:
            self.message = self.message + " (" + context + ")"
        super().__init__(self.message)

def scale(input_value, source_range, target_range, roundTo: int = None):
    """Scales a value to one range from another, optional bool to round the output.\n
    Example `scale(128, (0,255), (0,1), 1)` -> `0.5` # Scale 128 from the 0-255 range to the 0-1 range, rounding to one decimal."""
    source_min, source_max = source_range
    target_min, target_max = target_range

    # Ensure the input is within the source range
    if not (source_min <= input_value <= source_max):
        raise ValueError(f"Input value {input_value} is outside of source range {source_range}.")

    # Calculate the scale factor and the new value
    scale = (target_max - target_min) / (source_max - source_min)
    scaled_value = target_min + (input_value - source_min) * scale

    # Round the value if roundTo parameter is provided
    if roundTo is not None:
        scaled_value = round(scaled_value, roundTo)

    return scaled_value

def closest_ansi_color(ansi_dict, input_color):
    # Extract the RGB values from the input color, ignore alpha if present
    r, g, b = input_color[:3]
    
    # Function to compute Euclidean distance between two RGB colors
    def color_distance(c1, c2):
        i = 0
        for a, b in zip(c1, c2):
            i += (int(a) - int(b)) ** 2
        return math.sqrt(i)
        #math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
    # Initialize minimum distance and closest color index
    min_distance = float('inf')
    closest_color_index = None
    
    # Iterate over the ANSI dictionary to find the closest color
    for index, ansi_color in ansi_dict.items():
        ansi_rgb = tuple(map(int, ansi_color.split(',')))
        distance = color_distance((r, g, b), ansi_rgb)
        if distance < min_distance:
            min_distance = distance
            closest_color_index = index
    
    return closest_color_index

class Text():

    def __init__(self,terminal:object,enableAlpha=False,opacityFormat:str="dec"):
        if opacityFormat.lower() in ["dec","decimal",1]:
            opacityFormat = 1
        elif opacityFormat.lower() in ["8bit","eightbit",255]:
            opacityFormat = 255
        else:
            raise ValueError(f"Invalid value '{opacityFormat.lower()}' for 'opacityFormat'. Must be one of 'dec', 'decimal', '8bit', 'eightbit', 1, 255 !")
        self.terminal = terminal
        self.enableAlpha = enableAlpha
        self.cache_inst_jfwc = None #plc
        self.cache_indentified_tags = {}
        self.default_token_enc = "utf-8"
        self.unicodeCharErrorMode = "replace"
        self.pre_conf_load_values = {}

        self.symbols = {
            "esc": "\033",
            "esc+": "\033["
        }

        self.tokens = {
            "nl": ["\n", "ascii"],
            "esc": ["\u001b", "ascii"]
        }

        self.color_tags = {
            # As Specced
            "sf.black": "$30",
            "sf.red": "$31",
            "sf.green": "$32",
            "sf.yellow": "$33",
            "sf.blue": "$34",
            "sf.magenta": "$35",
            "sf.cyan": "$36",
            "sf.white": "$37",
            "sf.br_black": "$90",
            "sf.br_red": "$91",
            "sf.br_green": "$92",
            "sf.br_yellow": "$93",
            "sf.br_blue": "$94",
            "sf.br_magenta": "$95",
            "sf.br_cyan": "$96",
            "sf.br_white": "$97",

            "sb.black": "$40",
            "sb.red": "$41",
            "sb.green": "$42",
            "sb.yellow": "$43",
            "sb.blue": "$44",
            "sb.magenta": "$45",
            "sb.cyan": "$46",
            "sb.white": "$47",
            "sb.br_black": "$100",
            "sb.br_red": "$101",
            "sb.br_green": "$102",
            "sb.br_yellow": "$103",
            "sb.br_blue": "$104",
            "sb.br_magenta": "$105",
            "sb.br_cyan": "$106",
            "sb.br_white": "$107",

            # lib-stringTags notations (By common mappings in terminals)
            "f.black": "$30",
            "f.darkgray": "$90",
            "f.gray": "$37",
            "f.white": "$97",
            "f.darkred": "$31",
            "f.red": "$91",
            "f.darkmagenta": "$35",
            "f.magenta": "$95",
            "f.darkblue": "$34",
            "f.blue": "$94",
            "f.darkcyan": "$36",
            "f.cyan": "$96",
            "f.darkgreen": "$32",
            "f.green": "$92",
            "f.darkyellow": "$33",
            "f.yellow": "$93",

            "b.black": "$40",
            "b.darkgray": "$100",
            "b.gray": "$47",
            "b.white": "$107",
            "b.darkred": "$41",
            "b.red": "$101",
            "b.darkmagenta": "$45",
            "b.magneta": "$105",
            "b.darkblue": "$44",
            "b.blue": "$104",
            "b.darkcyan": "$46",
            "b.cyan": "$106",
            "b.darkgreen": "$42",
            "b.green": "$102",
            "b.darkyellow": "$43",
            "b.yellow": "$103",
        }

        self.format_tags = {
            # Basic
            "reset": "$0", #r
            "bold": "$1",
            "faint": "$2", #dim
            "italic": "$3",
            "underline": "$4",
            "blink": "$5",
            "strike": "$9", #strikethrough,strk

            # Off
            "normal": "$22", #bold_off,faint_off,italic_off
            "underline_off": "$24",
            "blink_off": "$25",
            "strike_off": "$29", #strikethrough_off,strk_off

            # Implementation, varies
            "uunb": "$21", #double_underline,not_bold_legacy
            "invert": "$7", #reverse
            "invert_off": "$27", #reverse_off
            "ninb": "$23", #no_italic_no_bl
            "overlined": "$53",
            "overlined_off": "$55",

            # Low Implementation
            "rapid_blink": "$6",
            "conceal": "$8", #hide
            "conceal_off": "$28", #hide_off,reveal,show

            # ScriptTypes Mintty
            "superscript": "$73",
            "subscript": "$74",
            "script_off": "$75",

            # Emoji-Variation-selector Mintty
            "framed": "$51",
            "encircled": "$52",
            "nfoe": "$54", #no_framed_no_encircled

            # Fonting
            "def_font": "$10",
            "alt_font_11": "$11",
            "alt_font_12": "$12",
            "alt_font_13": "$13",
            "alt_font_14": "$14",
            "alt_font_15": "$15",
            "alt_font_16": "$16",
            "alt_font_17": "$17",
            "alt_font_18": "$18",
            "alt_font_19": "$19",
            "fraktur": "$20",

            # Legacy.StringTagsCompat.PowershellCompat.Presets
            "p.formataccent": "$32;1",
            "p.tableheader": "$32;1",
            "p.erroraccent": "$36;1",
            "p.error": "$31;1",
            "p.warning": "$33;1",
            "p.verbose": "$33;1",
            "p.debug": "$33;1",
            "p.style": "$33;1",
            "fi.directory": "$44;1",
            "fi.symboliclink": "$36;1",
            "fi.executable": "$32;1"
        }

        self.mappings = {
            # Defaults
            "r": "format_tags@reset",

            "dim": "format_tags@faint",

            "strikethrough": "format_tags@strike",
            "strk": "format_tags@strike",

            "bold_off": "format_tags@normal",
            "faint_off": "format_tags@normal",
            "italic_off": "format_tags@normal",

            "strikethrough_off": "format_tags@strike_off",
            "strk_off": "format_tags@strike_off",

            "double_underline": "format_tags@uunb",
            "not_bold_legacy": "format_tags@uunb",

            "reverse": "format_tags@invert",
            "reverse_off": "format_tags@invert_off",

            "no_italic_no_bl": "format_tags@ninb",

            "hide": "format_tags@conceal",
            "hide_off": "format_tags@conceal_off",
            "reveal": "format_tags@conceal_off",
            "show": "format_tags@conceal_off",

            "no_framed_no_encircled": "format_tags@nfoe"
        }

        self.eightbit_to_rgb = {"0": "0,0,0", "1": "128,0,0", "2": "0,128,0", "3": "128,128,0", "4": "0,0,128", "5": "128,0,128", "6": "0,128,128", "7": "192,192,192", "8": "128,128,128", "9": "255,0,0", "10": "0,255,0", "11": "255,255,0", "12": "0,0,255", "13": "255,0,255", "14": "0,255,255", "15": "255,255,255", "16": "0,0,0", "17": "0,0,51", "18": "0,0,102", "19": "0,0,153", "20": "0,0,204", "21": "0,0,255", "22": "0,51,0", "23": "0,51,51", "24": "0,51,102", "25": "0,51,153", "26": "0,51,204", "27": "0,51,255", "28": "0,102,0", "29": "0,102,51", "30": "0,102,102", "31": "0,102,153", "32": "0,102,204", "33": "0,102,255", "34": "0,153,0", "35": "0,153,51", "36": "0,153,102", "37": "0,153,153", "38": "0,153,204", "39": "0,153,255", "40": "0,204,0", "41": "0,204,51", "42": "0,204,102", "43": "0,204,153", "44": "0,204,204", "45": "0,204,255", "46": "0,255,0", "47": "0,255,51", "48": "0,255,102", "49": "0,255,153", "50": "0,255,204", "51": "0,255,255", "52": "51,0,0", "53": "51,0,51", "54": "51,0,102", "55": "51,0,153", "56": "51,0,204", "57": "51,0,255", "58": "51,51,0", "59": "51,51,51", "60": "51,51,102", "61": "51,51,153", "62": "51,51,204", "63": "51,51,255", "64": "51,102,0", "65": "51,102,51", "66": "51,102,102", "67": "51,102,153", "68": "51,102,204", "69": "51,102,255", "70": "51,153,0", "71": "51,153,51", "72": "51,153,102", "73": "51,153,153", "74": "51,153,204", "75": "51,153,255", "76": "51,204,0", "77": "51,204,51", "78": "51,204,102", "79": "51,204,153", "80": "51,204,204", "81": "51,204,255", "82": "51,255,0", "83": "51,255,51", "84": "51,255,102", "85": "51,255,153", "86": "51,255,204", "87": "51,255,255", "88": "102,0,0", "89": "102,0,51", "90": "102,0,102", "91": "102,0,153", "92": "102,0,204", "93": "102,0,255", "94": "102,51,0", "95": "102,51,51", "96": "102,51,102", "97": "102,51,153", "98": "102,51,204", "99": "102,51,255", "100": "102,102,0", "101": "102,102,51", "102": "102,102,102", "103": "102,102,153", "104": "102,102,204", "105": "102,102,255", "106": "102,153,0", "107": "102,153,51", "108": "102,153,102", "109": "102,153,153", "110": "102,153,204", "111": "102,153,255", "112": "102,204,0", "113": "102,204,51", "114": "102,204,102", "115": "102,204,153", "116": "102,204,204", "117": "102,204,255", "118": "102,255,0", "119": "102,255,51", "120": "102,255,102", "121": "102,255,153", "122": "102,255,204", "123": "102,255,255", "124": "153,0,0", "125": "153,0,51", "126": "153,0,102", "127": "153,0,153", "128": "153,0,204", "129": "153,0,255", "130": "153,51,0", "131": "153,51,51", "132": "153,51,102", "133": "153,51,153", "134": "153,51,204", "135": "153,51,255", "136": "153,102,0", "137": "153,102,51", "138": "153,102,102", "139": "153,102,153", "140": "153,102,204", "141": "153,102,255", "142": "153,153,0", "143": "153,153,51", "144": "153,153,102", "145": "153,153,153", "146": "153,153,204", "147": "153,153,255", "148": "153,204,0", "149": "153,204,51", "150": "153,204,102", "151": "153,204,153", "152": "153,204,204", "153": "153,204,255", "154": "153,255,0", "155": "153,255,51", "156": "153,255,102", "157": "153,255,153", "158": "153,255,204", "159": "153,255,255", "160": "204,0,0", "161": "204,0,51", "162": "204,0,102", "163": "204,0,153", "164": "204,0,204", "165": "204,0,255", "166": "204,51,0", "167": "204,51,51", "168": "204,51,102", "169": "204,51,153", "170": "204,51,204", "171": "204,51,255", "172": "204,102,0", "173": "204,102,51", "174": "204,102,102", "175": "204,102,153", "176": "204,102,204", "177": "204,102,255", "178": "204,153,0", "179": "204,153,51", "180": "204,153,102", "181": "204,153,153", "182": "204,153,204", "183": "204,153,255", "184": "204,204,0", "185": "204,204,51", "186": "204,204,102", "187": "204,204,153", "188": "204,204,204", "189": "204,204,255", "190": "204,255,0", "191": "204,255,51", "192": "204,255,102", "193": "204,255,153", "194": "204,255,204", "195": "204,255,255", "196": "255,0,0", "197": "255,0,51", "198": "255,0,102", "199": "255,0,153", "200": "255,0,204", "201": "255,0,255", "202": "255,51,0", "203": "255,51,51", "204": "255,51,102", "205": "255,51,153", "206": "255,51,204", "207": "255,51,255", "208": "255,102,0", "209": "255,102,51", "210": "255,102,102", "211": "255,102,153", "212": "255,102,204", "213": "255,102,255", "214": "255,153,0", "215": "255,153,51", "216": "255,153,102", "217": "255,153,153", "218": "255,153,204", "219": "255,153,255", "220": "255,204,0", "221": "255,204,51", "222": "255,204,102", "223": "255,204,153", "224": "255,204,204", "225": "255,204,255", "226": "255,255,0", "227": "255,255,51", "228": "255,255,102", "229": "255,255,153", "230": "255,255,204", "231": "255,255,255", "232": "8,8,8", "233": "18,18,18", "234": "28,28,28", "235": "38,38,38", "236": "48,48,48", "237": "58,58,58", "238": "68,68,68", "239": "78,78,78", "240": "88,88,88", "241": "98,98,98", "242": "108,108,108", "243": "118,118,118", "244": "128,128,128", "245": "138,138,138", "246": "148,148,148", "247": "158,158,158", "248": "168,168,168", "249": "178,178,178", "250": "188,188,188", "251": "198,198,198", "252": "208,208,208", "253": "218,218,218", "254": "228,228,228", "255": "238,238,238"}
        self.eightbit_to_ansi_fg = {"0": 30, "1": 31, "2": 32, "3": 33, "4": 34, "5": 35, "6": 36, "7": 37, "8": 90, "9": 91, "10": 92, "11": 93, "12": 94, "13": 95, "14": 96, "15": 97, "16": 30, "17": 34, "18": 34, "19": 34, "20": 94, "21": 94, "22": 32, "23": 34, "24": 34, "25": 34, "26": 94, "27": 94, "28": 32, "29": 32, "30": 36, "31": 36, "32": 94, "33": 34, "34": 32, "35": 32, "36": 92, "37": 36, "38": 36, "39": 96, "40": 92, "41": 92, "42": 92, "43": 96, "44": 96, "45": 96, "46": 92, "47": 92, "48": 92, "49": 96, "50": 96, "51": 96, "52": 31, "53": 31, "54": 35, "55": 34, "56": 94, "57": 94, "58": 33, "59": 90, "60": 90, "61": 34, "62": 94, "63": 94, "64": 32, "65": 32, "66": 36, "67": 36, "68": 36, "69": 94, "70": 32, "71": 32, "72": 92, "73": 96, "74": 36, "75": 36, "76": 92, "77": 92, "78": 92, "79": 36, "80": 96, "81": 96, "82": 92, "83": 92, "84": 92, "85": 92, "86": 96, "87": 96, "88": 31, "89": 31, "90": 35, "91": 35, "92": 34, "93": 94, "94": 33, "95": 33, "96": 95, "97": 35, "98": 35, "99": 94, "100": 33, "101": 33, "102": 93, "103": 96, "104": 96, "105": 96, "106": 92, "107": 92, "108": 92, "109": 37, "110": 96, "111": 96, "112": 92, "113": 92, "114": 92, "115": 92, "116": 96, "117": 96, "118": 92, "119": 92, "120": 96, "121": 93, "122": 96, "123": 96, "124": 31, "125": 31, "126": 31, "127": 35, "128": 35, "129": 34, "130": 31, "131": 31, "132": 31, "133": 35, "134": 35, "135": 34, "136": 33, "137": 33, "138": 93, "139": 96, "140": 96, "141": 94, "142": 33, "143": 33, "144": 93, "145": 37, "146": 90, "147": 36, "148": 32, "149": 92, "150": 92, "151": 92, "152": 37, "153": 96, "154": 92, "155": 92, "156": 92, "157": 92, "158": 37, "159": 96, "160": 91, "161": 91, "162": 91, "163": 35, "164": 95, "165": 95, "166": 91, "167": 91, "168": 91, "169": 35, "170": 95, "171": 95, "172": 33, "173": 33, "174": 93, "175": 95, "176": 95, "177": 35, "178": 33, "179": 33, "180": 33, "181": 93, "182": 37, "183": 95, "184": 93, "185": 93, "186": 93, "187": 37, "188": 37, "189": 37, "190": 93, "191": 93, "192": 93, "193": 37, "194": 37, "195": 97, "196": 91, "197": 91, "198": 91, "199": 95, "200": 95, "201": 95, "202": 91, "203": 91, "204": 91, "205": 95, "206": 95, "207": 95, "208": 91, "209": 91, "210": 91, "211": 91, "212": 95, "213": 95, "214": 93, "215": 93, "216": 93, "217": 93, "218": 95, "219": 95, "220": 93, "221": 93, "222": 93, "223": 93, "224": 93, "225": 95, "226": 93, "227": 93, "228": 93, "229": 93, "230": 97, "231": 97, "232": 30, "233": 30, "234": 30, "235": 30, "236": 30, "237": 30, "238": 90, "239": 90, "240": 90, "241": 90, "242": 90, "243": 90, "244": 90, "245": 90, "246": 90, "247": 90, "248": 37, "249": 37, "250": 37, "251": 37, "252": 37, "253": 37, "254": 97, "255": 97}
        self.eightbit_to_ansi_bg = {"0": 40, "1": 41, "2": 42, "3": 43, "4": 44, "5": 45, "6": 46, "7": 47, "8": 100, "9": 101, "10": 102, "11": 103, "12": 104, "13": 105, "14": 106, "15": 107, "16": 40, "17": 44, "18": 44, "19": 44, "20": 104, "21": 104, "22": 42, "23": 44, "24": 44, "25": 44, "26": 104, "27": 104, "28": 42, "29": 42, "30": 46, "31": 46, "32": 104, "33": 44, "34": 42, "35": 42, "36": 102, "37": 46, "38": 46, "39": 106, "40": 102, "41": 102, "42": 102, "43": 106, "44": 106, "45": 106, "46": 102, "47": 102, "48": 102, "49": 106, "50": 106, "51": 106, "52": 41, "53": 41, "54": 45, "55": 44, "56": 104, "57": 104, "58": 43, "59": 100, "60": 100, "61": 44, "62": 104, "63": 104, "64": 42, "65": 42, "66": 46, "67": 46, "68": 46, "69": 104, "70": 42, "71": 42, "72": 102, "73": 106, "74": 46, "75": 46, "76": 102, "77": 102, "78": 102, "79": 46, "80": 106, "81": 106, "82": 102, "83": 102, "84": 102, "85": 102, "86": 106, "87": 106, "88": 41, "89": 41, "90": 45, "91": 45, "92": 44, "93": 104, "94": 43, "95": 43, "96": 105, "97": 45, "98": 45, "99": 104, "100": 43, "101": 43, "102": 103, "103": 106, "104": 106, "105": 106, "106": 102, "107": 102, "108": 102, "109": 47, "110": 106, "111": 106, "112": 102, "113": 102, "114": 102, "115": 102, "116": 106, "117": 106, "118": 102, "119": 102, "120": 106, "121": 103, "122": 106, "123": 106, "124": 41, "125": 41, "126": 41, "127": 45, "128": 45, "129": 44, "130": 41, "131": 41, "132": 41, "133": 45, "134": 45, "135": 44, "136": 43, "137": 43, "138": 103, "139": 106, "140": 106, "141": 104, "142": 43, "143": 43, "144": 103, "145": 47, "146": 100, "147": 46, "148": 42, "149": 102, "150": 102, "151": 102, "152": 47, "153": 106, "154": 102, "155": 102, "156": 102, "157": 102, "158": 47, "159": 106, "160": 101, "161": 101, "162": 101, "163": 45, "164": 105, "165": 105, "166": 101, "167": 101, "168": 101, "169": 45, "170": 105, "171": 105, "172": 43, "173": 43, "174": 103, "175": 105, "176": 105, "177": 45, "178": 43, "179": 43, "180": 43, "181": 103, "182": 47, "183": 105, "184": 103, "185": 103, "186": 103, "187": 47, "188": 47, "189": 47, "190": 103, "191": 103, "192": 103, "193": 47, "194": 47, "195": 107, "196": 101, "197": 101, "198": 101, "199": 105, "200": 105, "201": 105, "202": 101, "203": 101, "204": 101, "205": 105, "206": 105, "207": 105, "208": 101, "209": 101, "210": 101, "211": 101, "212": 105, "213": 105, "214": 103, "215": 103, "216": 103, "217": 103, "218": 105, "219": 105, "220": 103, "221": 103, "222": 103, "223": 103, "224": 103, "225": 105, "226": 103, "227": 103, "228": 103, "229": 103, "230": 107, "231": 107, "232": 40, "233": 40, "234": 40, "235": 40, "236": 40, "237": 40, "238": 100, "239": 100, "240": 100, "241": 100, "242": 100, "243": 100, "244": 100, "245": 100, "246": 100, "247": 100, "248": 47, "249": 47, "250": 47, "251": 47, "252": 47, "253": 47, "254": 107, "255": 107}

        self.ansi_fgs = [30,31,32,33,34,35,36,37, 90,91,92,93,94,95,96,97]
        self.ansi_bgs = [40,41,42,43,44,45,46,47, 100,101,102,103,104,105,106,107]

        self.palette = {}

        self.win_name_mapping = {
            "0": "Black",
            "1": "Blue",
            "2": "Green",
            "3": "Aqua",         #cyan
            "4": "Red",
            "5": "Purple",       #magenta
            "6": "Yellow",
            "7": "White",

            "8": "Gray",         #bright_black
            "9": "Light_Blue",   #bright_blue
            "A": "Light_Green",  #bright_green
            "B": "Light_Aqua",   #bright_cyan
            "C": "Light_Red",    #bright_red
            "D": "Light_Purple", #bright_magenta
            "E": "Light_Yellow", #bright_yellow
            "F": "Bright_White"
        }

        self.win_name_mapping_reversed = {}
        '''!FILLED ON INIT!'''
        for k,v in self.win_name_mapping.items():
            self.win_name_mapping_reversed[v] = k

        self.win_ansi_mapping_fg = {
            "Black": "30",
            "Blue": "34",
            "Green": "32",
            "Aqua": "36",
            "Red": "31",
            "Purple": "35",
            "Yellow": "33",
            "White": "37",

            "Gray": "90",
            "Light_Blue": "94",
            "Light_Green": "92",
            "Light_Aqua": "96",
            "Light_Red": "91",
            "Light_Purple": "95",
            "Light_Yellow": "93",
            "Bright_White": "97",
        }

        self.win_ansi_mapping_bg = {
            "Black": "40",
            "Blue": "44",
            "Green": "42",
            "Aqua": "46",
            "Red": "41",
            "Purple": "45",
            "Yellow": "43",
            "White": "47",

            "Gray": "100",
            "Light_Blue": "104",
            "Light_Green": "102",
            "Light_Aqua": "106",
            "Light_Red": "101",
            "Light_Purple": "105",
            "Light_Yellow": "103",
            "Bright_White": "107"
        }

    def load_config(self,configdict:dict):
        # Mappings
        if configdict.get("Mappings") != None:
            self.pre_conf_load_values["mappings"] = self.mappings.copy()
            self.mappings.update(configdict["Mappings"])
        # Palette
        if configdict.get("Palette") != None:
            self.pre_conf_load_values["palette"] = self.palette.copy()
            self.palette.update(configdict["Palette"])
        # Tokens
        if configdict.get("Tokens") != None:
            self.pre_conf_load_values["tokens"] = self.tokens.copy()
            self.tokens.update(configdict["Tokens"])
        # unicodeCharErrorMode
        if configdict.get("unicodeCharErrorMode") != None:
            self.pre_conf_load_values["unicodeCharErrorMode"] = self.unicodeCharErrorMode
            self.unicodeCharErrorMode = configdict["unicodeCharErrorMode"]
        # ColorTags
        if configdict.get("ColorTags") != None:
            self.pre_conf_load_values["color_tags"] = self.color_tags.copy()
            self.color_tags.update(configdict["ColorTags"])
        # FormatTags
        if configdict.get("FormatTags") != None:
            self.pre_conf_load_values["format_tags"] = self.format_tags.copy()
            self.format_tags.update(configdict["FormatTags"])
        # ConversionPalettes
        if configdict.get("ConversionPalettes") != None:
            # ConversionPalettes->EightBitToRGB
            if configdict["ConversionPalettes"].get("EightBitToRGB") != None:
                self.pre_conf_load_values["eightbit_to_rgb"] = self.eightbit_to_rgb.copy()
                self.eightbit_to_rgb.update(configdict["ConversionPalettes"]["EightBitToRGB"])
            # ConversionPalettes->EightBitToAnsiFG
            if configdict["ConversionPalettes"].get("EightBitToAnsiFG") != None:
                self.pre_conf_load_values["eightbit_to_ansi_fg"] = self.eightbit_to_ansi_fg.copy()
                self.eightbit_to_ansi_fg.update(configdict["ConversionPalettes"]["EightBitToAnsiFG"])
            # ConversionPalettes->EightBitToAnsiBG
            if configdict["ConversionPalettes"].get("EightBitToAnsiBG") != None:
                self.pre_conf_load_values["eightbit_to_ansi_bg"] = self.eightbit_to_ansi_bg.copy()
                self.eightbit_to_ansi_bg.update(configdict["ConversionPalettes"]["EightBitToAnsiBG"])
        # WinMapping
        if configdict.get("WinMapping") != None:
            # WinMapping->WinName
            if configdict["WinMapping"].get("WinName") != None:
                self.pre_conf_load_values["win_name_mapping"] = self.win_name_mapping.copy()
                self.win_name_mapping.update(configdict["WinMapping"]["WinName"])
            # WinMapping->WinAnsiFG
            if configdict["WinMapping"].get("WinAnsiFG") != None:
                self.pre_conf_load_values["win_ansi_mapping_fg"] = self.win_ansi_mapping_fg.copy()
                self.win_ansi_mapping_fg.update(configdict["WinMapping"]["WinAnsiFG"])
            # WinMapping->WinAnsiBG
            if configdict["WinMapping"].get("WinAnsiBG") != None:
                self.pre_conf_load_values["win_ansi_mapping_bg"] = self.win_ansi_mapping_bg.copy()
                self.win_ansi_mapping_bg.update(configdict["WinMapping"]["WinAnsiBG"])
        # InternalDefintions
        if configdict.get("InternalDefintions") != None:
            # InternalDefintions->AnsiFGs
            if configdict["InternalDefintions"].get("AnsiFGs") != None:
                self.pre_conf_load_values["ansi_fgs"] = self.ansi_fgs
                self.ansi_fgs.update(configdict["InternalDefintions"]["AnsiFGs"])
            # InternalDefintions->AnsiBGs
            if configdict["InternalDefintions"].get("AnsiBGs") != None:
                self.pre_conf_load_values["ansi_bgs"] = self.ansi_bgs
                self.ansi_bgs.update(configdict["InternalDefintions"]["AnsiBGs"])
        # InternalSymbols
        if configdict.get("InternalSymbols") != None:
            self.pre_conf_load_values["symbols"] = self.symbols.copy()
            self.symbols.update(configdict["InternalSymbols"])
        
    def reset_config(self):
        # Mappings
        if self.pre_conf_load_values.get("mappings") != None:
            self.mappings = self.pre_conf_load_values["mappings"]
            self.pre_conf_load_values.pop("mappings")
        # Palette
        if self.pre_conf_load_values.get("palette") != None:
            self.palette = self.pre_conf_load_values["palette"]
            self.pre_conf_load_values.pop("palette")
        # Tokens
        if self.pre_conf_load_values.get("tokens") != None:
            self.tokens = self.pre_conf_load_values["tokens"]
            self.pre_conf_load_values.pop("tokens")
        # unicodeCharErrorMode
        if self.pre_conf_load_values.get("unicodeCharErrorMode") != None:
            self.unicodeCharErrorMode = self.pre_conf_load_values["unicodeCharErrorMode"]
            self.pre_conf_load_values.pop("unicodeCharErrorMode")
        # ColorTags
        if self.pre_conf_load_values.get("color_tags") != None:
            self.color_tags = self.pre_conf_load_values["color_tags"]
            self.pre_conf_load_values.pop("color_tags")
        # FormatTags
        if self.pre_conf_load_values.get("format_tags") != None:
            self.format_tags = self.pre_conf_load_values["format_tags"]
            self.pre_conf_load_values.pop("format_tags")
        # ConversionPalettes
            # ConversionPalettes->EightBitToRGB
            if self.pre_conf_load_values.get("eightbit_to_rgb") != None:
                self.eightbit_to_rgb = self.pre_conf_load_values["eightbit_to_rgb"]
                self.pre_conf_load_values.pop("eightbit_to_rgb")
            # ConversionPalettes->EightBitToAnsiFG
            if self.pre_conf_load_values.get("eightbit_to_ansi_fg") != None:
                self.eightbit_to_ansi_fg = self.pre_conf_load_values["eightbit_to_ansi_fg"]
                self.pre_conf_load_values.pop("eightbit_to_ansi_fg")
            # ConversionPalettes->EightBitToAnsiBG
            if self.pre_conf_load_values.get("eightbit_to_ansi_bg") != None:
                self.eightbit_to_ansi_bg = self.pre_conf_load_values["eightbit_to_ansi_bg"]
                self.pre_conf_load_values.pop("eightbit_to_ansi_bg")
        # WinMapping
            # WinMapping->WinName
            if self.pre_conf_load_values.get("win_name_mapping") != None:
                self.win_name_mapping = self.pre_conf_load_values["win_name_mapping"]
                self.pre_conf_load_values.pop("win_name_mapping")
            # WinMapping->WinAnsiFG
            if self.pre_conf_load_values.get("win_ansi_mapping_fg") != None:
                self.win_ansi_mapping_fg = self.pre_conf_load_values["win_ansi_mapping_fg"]
                self.pre_conf_load_values.pop("win_ansi_mapping_fg")
            # WinMapping->WinAnsiBG
            if self.pre_conf_load_values.get("win_ansi_mapping_bg") != None:
                self.win_ansi_mapping_bg = self.pre_conf_load_values["win_ansi_mapping_bg"]
                self.pre_conf_load_values.pop("win_ansi_mapping_bg")
        # InternalDefintions
            # InternalDefintions->AnsiFGs
            if self.pre_conf_load_values.get("ansi_fgs") != None:
                self.ansi_fgs = self.pre_conf_load_values["ansi_fgs"]
                self.pre_conf_load_values.pop("ansi_fgs")
            # InternalDefintions->AnsiBGs
            if self.pre_conf_load_values.get("ansi_bgs") != None:
                self.ansi_fgs = self.pre_conf_load_values["ansi_bgs"]
                self.pre_conf_load_values.pop("ansi_bgs")
        # InternalSymbols
        if self.pre_conf_load_values.get("symbols") != None:
            self.symbols = self.pre_conf_load_values["symbols"]
            self.pre_conf_load_values.pop("symbols")

    def capitalize_first_letter(self,string):
        # Handle WinShort
        if string.startswith("%f"):
            return "%f"+self.capitalize_first_letter(string.replace("%f","",1))
        elif string.startswith("%b"):
            return "%b"+self.capitalize_first_letter(string.replace("%f","",1))
        # Check if the string is not empty and the first character is a lowercase letter
        if string and string[0].isalpha() and string[0].islower():
            # Capitalize the first character and concatenate it with the rest of the string
            string = string[0].upper() + string[1:]
        return string

    def _arstrip(self,string:str,token:str,amnt:int=-1):
        """[TEMP] Implements rstrip but taking an amnt of the char to remove.\n
        Multiple chars not permitted (works like .replace), negative amounts removes al."""
        # FIND BETTER IMPLEMENTATION
        if amnt < 0:
            return string[::-1].replace(token,"")[::-1]
        else:
            return string[::-1].replace(token,"",amnt)[::-1]

    def ansi_str_to_common(self,ansiStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle $𝑥ₐ -> #ansi.𝑥ₐm
        if not ansiStr.startswith("$"):
            ansiStr = self._arstrip( ansiStr.strip().replace(self.symbols["esc+"],""), "m",1)
        else:
            ansiStr = ansiStr.replace("$","",1)
        return "#ansi." + ansiStr + "m"
    
    def ansi_common_to_str(self,ansiCommon:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle #ansi.𝑥ₐm -> \033[𝑥ₐm
        if not ansiCommon.startswith("#ansi."):
            raise InvalidCommonOrNativeFormat
        # Ensure m in output
        ansi = ansiCommon.strip().replace("#ansi.","",1)
        if not ansi.endswith("m"):
            ansi = ansi + "m"
        return self.symbols["esc+"] + ansi
    
    def eightbit_str_to_common(self,eightbitStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle $38;5;𝑥₈ -> f#8bit.𝑥₈
        #        $48;5;𝑥₈ -> b#8bit.𝑥₈
        #        Fallbacks to #ansi.𝑥ₐ;𝑥ₐ;𝑥₈m
        if not eightbitStr.startswith("$"):
            eightbitStr = self._arstrip( eightbitStr.strip().replace(self.symbols["esc+"],""), "m",1)
        else:
            eightbitStr = eightbitStr.strip().replace("$","",1)
        if eightbitStr.endswith("m"):
            eightbitStr = self._arstrip(eightbitStr,"m",1)
        # fg
        if eightbitStr.startswith("38;5;"):
            return "f#8bit." + eightbitStr.replace("38;5;","",1)
        # bg
        elif eightbitStr.startswith("48;5;"):
            return "b#8bit." + eightbitStr.replace("48;5;","",1)
        # fallback to ANSI
        else:
            return "#ansi." + eightbitStr + "m"

    def eightbit_common_to_str(self,eightbitCommon:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle f#8bit.𝑥₈ -> $38;5;𝑥₈
        #        b#8bit.𝑥₈ -> $48;5;𝑥₈
        #        Fallbacks to \033[𝑥ₐ;𝑥ₐ;𝑥₈m
        eightbitCommon = eightbitCommon.strip()
        if eightbitCommon.endswith("m"):
            eightbitCommon = self._arstrip(eightbitCommon,"m",1)
        # fg
        if eightbitCommon.startswith("f#8bit."):
            return self.symbols["esc+"] + "38;5;" + eightbitCommon.replace("f#8bit.","",1) + "m"
        # bg
        elif eightbitCommon.startswith("b#8bit."):
            return self.symbols["esc+"] + "48;5;" + eightbitCommon.replace("b#8bit.","",1) + "m"
        # fallback handling
        elif eightbitCommon.startswith("#ansi."):
            return self.symbols["esc+"] + eightbitCommon.replace("#ansi.","",1) + "m"
        # error
        else:
            raise InvalidCommonOrNativeFormat(context="INVALID_COMMON.NON_8BIT_OR_ANSI")

    def hex_to_rgba_components(self, hexCode, stripHash: bool = True):
        '''ASSUMES INPUT IS VALID FORMAT; NO HASHTAG (#); ALPHA PERMITTED, None IF OMITTED.'''
        # Strip the hash symbol if strip_hash is True and hex code starts with '#'
        if stripHash and hexCode.startswith('#'):
            hexCode = hexCode[1:]
        
        # Validate the length of the hex code
        if len(hexCode) not in (6, 8):
            raise ValueError("Hex code must be 6 or 8 characters long.")

        # Convert the hex code to integers for each component
        r = int(hexCode[0:2], 16)
        g = int(hexCode[2:4], 16)
        b = int(hexCode[4:6], 16)

        # If the length is 8, include the alpha channel as an integer (0-255)
        if len(hexCode) == 8:
            a = int(hexCode[6:8], 16)
            return [r, g, b, a]
        else:
            return [r, g, b, None]

    def rgba_components_to_hex(self, rgb, include_hash: bool = False):
        '''ASSUMES INPUT IS VALID FORMAT; ALPHA PERMITTED, OMITTED IF NOT GIVEN.'''
        # Ensure the input is a list with either 3 or 4 elements
        if len(rgb) not in (3, 4):
            raise ValueError("Input must be a list with 3 (RGB) or 4 (RGBA) elements.")
        
        if len(rgb) == 4:
            if rgb[-1] == None:
                rgb.pop(-1)
        
        # Convert each component to a two-digit hex value
        hex_code = "{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2])
        
        # If alpha channel is present, include it in the hex code
        if len(rgb) == 4:
            hex_code += "{:02X}".format(rgb[3])
        
        # Add the hash symbol if include_hash is True
        if include_hash:
            hex_code = "#" + hex_code

        return hex_code
    
    def hex_str_to_rgb_common(self,hexStr:str,yeildTypeInt:bool=False) -> Union[str,Tuple[str,int]]:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle #(!)𝑟𝑟𝑔𝑔𝑏𝑏   -> <g>#rgb(𝑅,𝐺,𝐵)
        #        #(!)𝑟𝑟𝑔𝑔𝑏𝑏𝑎𝑎 -> <g>#rgb(𝑅,𝐺,𝐵,𝑎)
        # 𝒶𝓁𝓅𝒽𝒶 gets omitted if not enabled.
        hexStr = hexStr.strip()
        if hexStr.startswith("#"):
            # bg
            if hexStr.startswith("#!"):
                hexStr = hexStr.replace("#!","",1)
                r,g,b,a = self.hex_to_rgba_components(hexStr)
                if len(hexStr) == 8: # alpha
                    if self.enableAlpha == True:
                        if yeildTypeInt == True:
                            return f"b#rgb({r},{g},{b},{a})",1
                        else:
                            return f"b#rgb({r},{g},{b},{a})"
                    else:
                        if yeildTypeInt == True:
                            return f"b#rgb({r},{g},{b})",0
                        else:
                            return f"b#rgb({r},{g},{b})"
                elif len(hexStr) == 6: # no-alpha
                    if yeildTypeInt == True:
                        return f"b#rgb({r},{g},{b})",0
                    else:
                        return f"b#rgb({r},{g},{b})"
                else: # fallback
                    raise InvalidCommonOrNativeFormat(context="NON_HEX.INVALID_LENGTH")
            # fg
            else:
                hexStr = hexStr.replace("#","",1)
                r,g,b,a = self.hex_to_rgba_components(hexStr)
                if len(hexStr) == 8: # alpha
                    if self.enableAlpha == True:
                        if yeildTypeInt == True:
                            return f"f#rgb({r},{g},{b},{a})",1
                        else:
                            return f"f#rgb({r},{g},{b},{a})"
                    else:
                        if yeildTypeInt == True:
                            return f"f#rgb({r},{g},{b})",0
                        else:
                            return f"f#rgb({r},{g},{b})"
                elif len(hexStr) == 6: # no-alpha
                    if yeildTypeInt == True:
                        return f"f#rgb({r},{g},{b})",0
                    else:
                        return f"f#rgb({r},{g},{b})"
                else: # fallback
                    raise InvalidCommonOrNativeFormat(context="NON_HEX.INVALID_LENGTH")
        else:
            raise InvalidCommonOrNativeFormat(context="NON_HEX")

    def rgb_common_to_rgb_str(self,rgbCommon:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle <g>#rgb(𝑅,𝐺,𝐵)   -> \033[x8;2;𝑅,𝐺,𝐵m
        #        <g>#rgb(𝑅,𝐺,𝐵,𝑎) -> \033[x8;2;𝑅,𝐺,𝐵m
        # 𝒶𝓁𝓅𝒽𝒶 gets omitted.
        rgbCommon = rgbCommon.strip()
        if not rgbCommon.startswith("f#rgb") and not rgbCommon.startswith("b#rgb"):
            raise InvalidCommonOrNativeFormat(context="INVALID_COMMON.NON_RGB")
        # extract values
        ground = "f"
        if rgbCommon.startswith("f#rgb("):
            rgbCommon = rgbCommon.replace("f#rgb(","",1)
            ground = "f"
        elif rgbCommon.startswith("b#rgb("):
            rgbCommon = rgbCommon.replace("b#rgb(","",1)
            ground = "b"
        rgbCommon = self._arstrip(rgbCommon,")",1)
        if ground == "f":
            return self.symbols["esc+"]+"38;2;"+rgbCommon.replace(",",";") + "m"
        elif ground == "b":
            return self.symbols["esc+"]+"48;2;"+rgbCommon.replace(",",";") + "m"
        

    def hex_str_to_rgb_str(self,hexStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle #𝑟𝑟𝑔𝑔𝑏𝑏(𝑎𝑎)  -> $38;2;𝑅;𝐺;𝐵(m)
        #        #!𝑟𝑟𝑔𝑔𝑏𝑏(𝑎𝑎) -> $48;2;𝑅;𝐺;𝐵(m)
        # 𝒶𝓁𝓅𝒽𝒶 gets omitted.
        hexStr = hexStr.strip()
        if hexStr.startswith("#"):
            # bg
            if hexStr.startswith("#!"):
                hexStr = hexStr.replace("#!","",1)
                r,g,b,_ = self.hex_to_rgba_components(hexStr)
                if not len(hexStr) in (6,8):
                    raise InvalidCommonOrNativeFormat(context="NON_HEX.INVALID_LENGTH")
                return self.symbols["esc+"] + f"48;2;{r};{g};{b}m"
            # fg
            else:
                hexStr = hexStr.replace("#","",1)
                r,g,b,_ = self.hex_to_rgba_components(hexStr)
                if not len(hexStr) in (6,8):
                    raise InvalidCommonOrNativeFormat(context="NON_HEX.INVALID_LENGTH")
                return self.symbols["esc+"] + f"38;2;{r};{g};{b}m"
        else:
            raise InvalidCommonOrNativeFormat(context="NON_HEX")

    def rgb_str_to_hex_str(self,rgbStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle $38;2;𝑅;𝐺;𝐵(m) -> #𝑟𝑟𝑔𝑔𝑏𝑏
        #        $48;2;𝑅;𝐺;𝐵(m) -> #!𝑟𝑟𝑔𝑔𝑏𝑏
        if not rgbStr.startswith("$"):
            rgbStr = self._arstrip( rgbStr.strip().replace(self.symbols["esc+"],""), "m",1)
        else:
            rgbStr = rgbStr.strip().replace("$","",1)
        if not rgbStr.startswith("38;2;") and not rgbStr.startswith("48;2;"):
            raise InvalidCommonOrNativeFormat(context="INVALID_COMMON.NON_RGB")
        # extract values
        ground = "f"
        if rgbStr.startswith("38;2;"):
            rgbStr = rgbStr.replace("38;2;","",1)
            ground = "f"
        elif rgbStr.startswith("48;2;"):
            rgbStr = rgbStr.replace("48;2;","",1)
            ground = "b"
        if rgbStr.endswith("m"):
            rgbStr = self._arstrip(rgbStr,"m",1)
        components = rgbStr.split(";")
        hex = self.rgba_components_to_hex(components)
        if ground == "b":
            hex = "#!" + hex
        elif ground == "f":
            hex = "#" + hex
        return hex

    def win_str_to_common(self,winStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle %<g>𝑥ᵥ -> <g>#win.𝑥ᵥ
        #        %<g>𝑛ᵥ -> <g>#win.𝑛ᵥ
        winStr = winStr.strip()
        winStr = self.capitalize_first_letter(winStr)
        if not (winStr.startswith("%f") or winStr.startswith("%b")):
            raise InvalidCommonOrNativeFormat(context="NON_WIN")
        ground = "f"
        if winStr.startswith("%f"):
            winStr = winStr.replace("%f","",1)
            ground = "f"
        elif winStr.startswith("%b"):
            winStr = winStr.replace("%b","",1)
            ground = "b"
        if winStr in self.win_name_mapping.keys():
            return ground + "#win." + winStr
        elif winStr in self.win_name_mapping.values():
            if len(self.win_name_mapping) < len(self.win_name_mapping_reversed):
                raise Exception("Invalid mappings, have you inited the class?")
            return ground + "#win." + self.win_name_mapping_reversed[winStr]
        else:
            raise InvalidCommonOrNativeFormat(context="NON_WIN.INVALID_VALUE")

    def win_common_to_str(self,winCommon:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle <g>#win.𝑥ᵥ -> %<g>𝑥ᵥ
        winCommon = winCommon.strip()
        if winCommon.startswith("f#win."):
            winCommon = winCommon.replace("f#win.","",1)
            if winCommon in self.win_name_mapping.values():
                if len(self.win_name_mapping) < len(self.win_name_mapping_reversed):
                    raise Exception("Invalid mappings, have you inited the class?")
                winCommon = self.win_name_mapping_reversed[winCommon]
            return "%f" + winCommon

        elif winCommon.startswith("b#win."):
            winCommon = winCommon.replace("b#win.","",1)
            if winCommon in self.win_name_mapping.values():
                if len(self.win_name_mapping) < len(self.win_name_mapping_reversed):
                    raise Exception("Invalid mappings, have you inited the class?")
                winCommon = self.win_name_mapping_reversed[winCommon]
            return "%b" + winCommon
        else:
            raise InvalidCommonOrNativeFormat(context="INVALID_COMMON.NON_WIN")

    def win_str_to_ansi_str(self,winStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle %<g>𝑥ᵥ -> \033[𝑥ₐm
        #        %<g>𝑛ᵥ -> \033[𝑥ₐm
        winStr = winStr.strip()
        winStr = self.capitalize_first_letter(winStr)
        ground = "f"
        if winStr.startswith("%f"):
            winStr = winStr.replace("%f","",1)
            ground = "f"
        elif winStr.startswith("%b"):
            winStr = winStr.replace("%b","",1)
            ground = "b"
        else:
            raise InvalidCommonOrNativeFormat(context="NON_WIN")
        if winStr in self.win_name_mapping.keys():
            winStr = self.win_name_mapping[winStr]
        if ground == "f":
            return self.symbols["esc+"] + self.win_ansi_mapping_fg[winStr] + "m"
        else:
            return self.symbols["esc+"] + self.win_ansi_mapping_bg[winStr] + "m"
        
    def win_str_to_ansi_common(self,winStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle %<g>𝑥ᵥ -> <g>#ansi.𝑥ₐm
        #        %<g>𝑛ᵥ -> <g>#ansi.𝑥ₐm
        winStr = winStr.strip()
        winStr = self.capitalize_first_letter(winStr)
        ground = "f"
        if winStr.startswith("%f"):
            winStr = winStr.replace("%f","",1)
            ground = "f"
        elif winStr.startswith("%b"):
            winStr = winStr.replace("%b","",1)
            ground = "b"
        else:
            raise InvalidCommonOrNativeFormat(context="NON_WIN")
        if winStr in self.win_name_mapping.keys():
            winStr = self.win_name_mapping[winStr]
        if ground == "f":
            return "#ansi." + self.win_ansi_mapping_fg[winStr] + "m"
        else:
            return "#ansi." + self.win_ansi_mapping_bg[winStr] + "m"
        
    def win_common_to_ansi_common(self,winStr:str) -> str:
        '''ASSUMES INPUT IS VALID FORMAT'''
        # Handle <g>#win.𝑥ᵥ -> <g>#ansi.𝑥ₐm
        #        <g>#win.𝑛ᵥ -> <g>#ansi.𝑥ₐm
        winStr = winStr.strip()
        ground = "f"
        if winStr.startswith("f#win."):
            winStr = winStr.replace("f#win.","",1)
            ground = "f"
        elif winStr.startswith("b#win."):
            winStr = winStr.replace("b#win.","",1)
            ground = "b"
        else:
            raise InvalidCommonOrNativeFormat(context="NON_WIN")
        if winStr in self.win_name_mapping.keys():
            winStr = self.win_name_mapping[winStr]
        if ground == "f":
            return "#ansi." + self.win_ansi_mapping_fg[winStr] + "m"
        else:
            return "#ansi." + self.win_ansi_mapping_bg[winStr] + "m"


    def rgb_to_closest_eightbit(self,rgb:list) -> int:
        # Handle [𝑅,𝐺,𝐵]   ⥲ 𝑥₈
        #        [𝑅,𝐺,𝐵,𝑎] ⥲ 𝑥₈
        # 𝒶𝓁𝓅𝒽𝒶 gets omitted if not enabled.
        return int(closest_ansi_color(self.eightbit_to_rgb,rgb))

    def eightbit_to_closest_ansi(self,eightbit:int,ground="fg") -> int:
        # Handle 𝑥₈ ⥲ 𝑥ₐ
        if ground in [1,"f","fg","F","Fg","fG","FG"]:
            return self.eightbit_to_ansi_fg[str(eightbit)]
        elif ground in [2,"b","bg","B","Bg","bG","BG"]:
            return self.eightbit_to_ansi_bg[str(eightbit)]
        else:
            raise InvalidCommonOrNativeFormat(context="INVALID_GROUND")

    # as defined in tags and palette
    def ansi_to_closest_eightbit(self,ansi:int,ground="fg") -> Union[int,None]:
        ansi = int(ansi)
        # Handle 𝑥ₐ ⥲ 𝑥₈
        if ground in [1,"f","fg","F","Fg","fG","FG"]:
            for k,v in self.eightbit_to_ansi_fg.items():
                if v == ansi: return int(k)
                else: return None
        elif ground in [2,"b","bg","B","Bg","bG","BG"]:
            for k,v in self.eightbit_to_ansi_bg.items():
                if v == ansi: return int(k)
                else: return None
        else:
            raise InvalidCommonOrNativeFormat(context="INVALID_GROUND")

    # as defined in tags and palette
    def eightbit_to_closest_rgb(self,eightbit:int) -> list:
        # Handle 𝑥₈ -> [𝑅,𝐺,𝐵]
        return self.eightbit_to_rgb[str(eightbit)].split(",")

    def rgb_components_to_str(self,components:list,ground="fg") -> str:
        # Handle fg,[𝑅,𝐺,𝐵,(a)] -> \033[38;2;𝑅;𝐺;𝐵(m)
        #        bg,[𝑅,𝐺,𝐵,(a)] -> \033[48;2;𝑅;𝐺;𝐵(m)
        # 𝒶𝓁𝓅𝒽𝒶 gets omitted if not enabled.
        if ground in [1,"f","fg","F","Fg","fG","FG"]:
            p = "38;2;"
        elif ground in [2,"b","bg","B","Bg","bG","BG"]:
            p = "48;2;"
        return self.symbols["esc+"] + p + ";".join(components[0:3]) + "m"

    def eightbit_num_to_str(self,eightbit:int,ground="fg") -> str:
        # Handle 𝑥₈ -> \033[38;5;𝑥₈(m)
        #        𝑥₈ -> \033[48;5;𝑥₈(m)
        if ground in [1,"f","fg","F","Fg","fG","FG"]:
            p = "38;5;"
        elif ground in [2,"b","bg","B","Bg","bG","BG"]:
            p = "48;5;"
        return self.symbols["esc+"] + p + str(eightbit) + "m"
    
    def ansi_num_to_str(self,ansi:int) -> str:
        return self.symbols["esc+"] + str(ansi) + "m"
    
    def colorama_justfix(self,forcePass=False,noCache=False):
        try:
            if self.cache_inst_jfwc == None or noCache == True:
                try:
                    from colorama import just_fix_windows_console as jfwc
                except ImportError:
                    jfwc = self.terminal.importa_instance.autopipImport("colorama",attr="just_fix_windows_console")
                self.cache_inst_jfwc = jfwc
            else:
                jfwc = self.cache_inst_jfwc
            if forcePass == True or self.terminal.legacy_windows == True:
                jfwc()
                return True
            return False
        except:
            return False

    def filter_tokens(self,forEncoding:str,replace:bool=False,_retCoded:bool=False,asciiOnly:bool=False) -> dict:
        """Function that returns the defined tokens that is allowed on your current output encoding. Returns as '<tagName>':'<value>'"""
        output = dict()
        for name,v in self.tokens.items():
            value = None
            enc = None
            
            if type(v) == str:
                value = v
                enc = self.default_token_enc
                if enc.lower() == "mirror": enc = self.terminal.encoding
            elif type(v) == list:
                if len(v) > 1:
                    value = v[0]
                    enc = v[1]
                else:
                    value = v[0]
                    enc = self.default_token_enc
                    if enc.lower() == "mirror": enc = self.terminal.encoding
            
            if asciiOnly == True and enc != None:
                enc = "ascii"

            if enc != None:
                try:
                    # Encode the string with the specified encoding
                    encodedValue = value.encode(enc)
                    # Decode it using the forEncoding (system encoding)
                    decodedValue = encodedValue.decode(forEncoding)
                    if _retCoded == True:
                        output[name] = decodedValue
                    else:
                        output[name] = value
                except (UnicodeEncodeError, UnicodeDecodeError):
                    if replace == True:
                        # Try to decode with errors='replace'
                        try:
                            # Use replace to handle encoding issues
                            decodedValue = value.encode(enc, errors='replace').decode(forEncoding, errors='replace')
                            output[name] = decodedValue
                        except UnicodeDecodeError:
                            pass
        return output

    def tag_extractor(self,s) -> list:
        # This regex pattern matches innermost tags
        pattern = re.compile(r'\{([^{}]*)\}')
        return pattern.findall(s)

    def syntx_str(self,string:str) -> str:
        """$<ansi> -> ^[<ansi>m"""
        if string.lstrip().startswith("$"):
            return self.symbols["esc+"] + string.replace("$","",1) + "m"
        elif string.lstrip().startswith("#ansi."):
            return self.ansi_common_to_str(string)
        return string

    def syntx_common(self,string:str) -> str:
        """$<ansi> -> #ansi.<ansi>m"""
        if string.lstrip().startswith("$"):
            return "#ansi." + string.replace("$","",1) + "m"
        elif string.lstrip().startswith(self.symbols["esc+"]):
            return "#ansi." + string.replace(self.symbols["esc+"],"",1) + "m"
        return string

    def identify_tag(self,tag:str) -> Tuple[Literal["WinShort","WindowsName","WindowsNum","Ansi","8bit","RGB","RGBa","ShortRGB","ShortRGBa","HEX","HEXa","plc"],Union[str,None],str]:
        """Returns the valuetype for a tag's value."""
        if tag.startswith("%f"):
            return "WinShort","f",tag.replace("%f","",1)
        elif tag.startswith("%b"):
            return "WinShort","b",tag.replace("%b","",1)

        elif tag.startswith("f#win."):
            if tag.replace("f#win.","",1).isdigit():
                return "WindowsNum","f",tag.replace("f#win.","",1)
            else:
                return "WindowsName","f",tag.replace("f#win.","",1)
        elif tag.startswith("b#win."):
            if tag.replace("b#win.","",1).isdigit():
                return "WindowsNum","b",tag.replace("b#win.","",1)
            else:
                return "WindowsName","b",tag.replace("b#win.","",1)

        elif tag.startswith("#ansi."):
            _t = tag.replace("#ansi.","",1)
            if _t.endswith("m"): _t = _t.rstrip("m")
            return "Ansi",None,_t

        elif tag.startswith("f#8bit."):
            return "8bit","f",tag.replace("f#8bit.","",1)
        elif tag.startswith("b#8bit."):
            return "8bit","b",tag.replace("b#8bit.","",1)

        elif tag.startswith("#!"):
            s_ = tag.replace("#!","",1)
            if len(s_) <= 6:
                return "HEX","b",s_
            else:
                return "HEXa","b",s_
        elif tag.startswith("#"):
            s_ = tag.replace("#","",1)
            if len(s_) <= 6:
                return "HEX","f",s_
            else:
                return "HEXa","f",s_

        elif tag.startswith("f#rgb("):
            parsed = tag.replace("f#rgb(","",1).rstrip(")")
            if len(parsed.split(",")) > 3:
                return "RGBa","f",parsed
            else:
                return "RGB","f",parsed
        elif tag.startswith("b#rgb("):
            parsed = tag.replace("b#rgb(","",1).rstrip(")")
            if len(parsed.split(",")) > 3:
                return "RGBa","b",parsed
            else:
                return "RGB","b",parsed

        elif tag.startswith("f#rgb;"):
            parsed = tag.replace("f#rgb;","",1)
            if len(parsed.split(";")) > 3:
                return "ShortRGBa","f",parsed
            else:
                return "ShortRGB","f",parsed
        elif tag.startswith("b#rgb;"):
            parsed = tag.replace("b#rgb;","",1)
            if len(parsed.split(";")) > 3:
                return "ShortRGBa","b",parsed
            else:
                return "ShortRGB","b",parsed

        elif tag.startswith("rgb."):
            return "stringTags.rgb","f",tag.replace("rgb.","",1)
        elif tag.startswith("rgb!"):
            return "stringTags.rgb","b",tag.replace("rgb!","",1)
        return "plc",None,""

    def identify_tag_cached(self,tag:str) -> tuple:
        """Returns the valuetype for a tag's value. (cached)"""
        if tag in self.cache_indentified_tags.keys():
            return self.cache_indentified_tags[tag]
        else:
            res = self.identify_tag(tag)
            self.cache_indentified_tags[tag] = res
            return res

    def get_string_for_paletted_value(self,commonValue:str,valuetype:str,skipPalette:bool=False) -> str:
        """Returns the correct string for a paletted value."""
        query = None
        prefix = ""
        if commonValue in self.palette.keys():
            query = commonValue
        elif "#"+commonValue.split("#")[1] in self.palette.keys():
            query = "#"+commonValue.split("#")[1]
            prefix = commonValue.split("#")[0]
        if valuetype == "8bit":
            if query != None and skipPalette != True:
                return self.get_tag_value("",True,_value=prefix+self.palette[query])
            else:
                return self.eightbit_common_to_str(commonValue)
        elif valuetype == "Ansi":
            if query != None and skipPalette != True:
                return self.get_tag_value("",True,_value=prefix+self.palette[query])
            else:
                return self.ansi_common_to_str(commonValue)

    # Repl format and color taking into account Palette and Mappings.
    def get_tag_value(self,tag:str,skipPalette:bool=False,forceUpConv:bool=False,stripTokens:bool=False,_value=None) -> str:
        """Gets the value for a non-token tag."""
        if stripTokens == True: return ""
        # Resolve mappings and value
        if _value == None:
            if tag in self.mappings.keys():
                group,tag = self.mappings[tag].split("@")
                if group == "color_tags":
                    # If no_color just return ""
                    if self.terminal.no_color == True or self.terminal.output_mode in ["none","formatting-only"]:
                        return ""
                    value = self.color_tags[tag]
                elif group == "format_tags":
                    if self.terminal.output_mode in ["none","color-only"]:
                        return ""
                    value = self.format_tags[tag]
                else:
                    value = None
            else:
                if tag in self.color_tags.keys():
                    value = self.color_tags[tag]
                elif tag in self.format_tags.keys():
                    value = self.format_tags[tag]
                else:
                    value = None
        else:
            value = _value
        if value != None:
            value = self.syntx_common(value)

        # Identify type
        valuetype = "plc"
        parsed = ""
        ground = ""
        if value == None:
            valuetype,ground,parsed = self.identify_tag_cached(tag)
            if valuetype == None or valuetype == "plc":
                value = None
            else:
                value = tag
        else:
            valuetype,ground,parsed = self.identify_tag_cached(value)

        # No_Color
        if self.terminal.no_color == True:
            if valuetype != "Ansi":
                return ""
            else:
                # Check if formatter?
                if value in self.format_tags.values() or "$"+parsed in self.format_tags.values() or self.symbols["esc+"]+parsed+"m" in self.format_tags.values(): pass
                else:
                    return ""

        # Convert
        ## WindowsShort -> WindowsName
        if valuetype == "WinShort":
            value = self.win_str_to_common(value)
            valuetype = "WindowsName"
        ## WindowsName/WindowsNum -> Ansi
        if valuetype == "WindowsName" or valuetype == "WindowsNum":
            value = self.win_common_to_ansi_common(value)
            valuetype = "Ansi"
        ## ShortRGB/ShortRGBa -> RGB/RGBa
        elif valuetype == "ShortRGB":
            value = ground+"#rgb("+parsed.replace(";",",")+")"
            parsed = parsed.replace(";",",")
            valuetype = "RGB"
        elif valuetype == "ShortRGBa":
            value = ground+"#rgb("+parsed.replace(";",",")+")"
            parsed = parsed.replace(";",",")
            valuetype = "RGBa"
        ## HEX/HEXa -> RGB/RGBa
        elif valuetype == "HEX":
            value,ti = self.hex_str_to_rgb_common(value,True)
            parsed = value.split("#")[1].replace("rgb(","",1).rstrip(")")
            if ti == 1:
                valuetype = "RGBa"
            else:
                valuetype = "RGB"
        ## stringTags.rgb -> RGB
        elif valuetype == "stringTags.rgb":
            if ground == "f":
                value = "f#rgb("+parsed.replace(";",",")+")"
                parsed = parsed.replace(";",",")
            elif ground == "b":
                value = "b#rgb("+parsed.replace(";",",")+")"
                parsed = parsed.replace(";",",")
            valuetype = "RGB"
        ## WHY DID MATCH/CASE NOT WORK HERE!?
        if self.terminal.color_system == self.terminal.COLOR_SYSTEMS["truecolor"]:  # TRUECOLOR
            # Ansi -> AnsiStr
            if valuetype == "Ansi":
                if forceUpConv == True:
                    # Ansi -> 8bit -> RGBStr/(AnsiStr)
                    _t = value.replace("#ansi.","",1)
                    ansiint = int(_t.rstrip("m")) if _t.endswith("m") else int(_t)
                    if ground == None or ground == "":
                        ground_ = "f" if ansiint in self.ansi_fgs else "b"
                    else:
                        ground_ = ground
                    eightbit = self.ansi_to_closest_eightbit( ansiint, ground_ )
                    if eightbit == None:
                        return self.ansi_num_to_str(ansiint)
                    components = self.eightbit_to_closest_rgb(eightbit)
                    return self.rgb_components_to_str(components)
                else:
                    return self.get_string_for_paletted_value(value,valuetype,skipPalette)
            # 8bit -> 8bitStr
            elif valuetype == "8bit":
                if forceUpConv == True:
                    # 8bit -> RGBstr
                    components = self.eightbit_to_closest_rgb( int(parsed) )
                    return self.rgb_components_to_str(components)
                else:
                    return self.get_string_for_paletted_value(value,valuetype,skipPalette)
            # RGB  -> RGBStr
            elif valuetype == "RGB":
                return self.rgb_common_to_rgb_str(value)
            # RGBa -> RGBStr,(alpha_notation)
        elif self.terminal.color_system == self.terminal.COLOR_SYSTEMS["256"]:  # EIGHT_BIT
            # RGB  -> 8bitStr
            if valuetype == "RGB":
                return self.eightbit_num_to_str(self.rgb_to_closest_eightbit(parsed.split(",")),ground)
            # 8bit -> 8bitStr
            elif valuetype == "8bit":
                return self.eightbit_common_to_str(value)
            # Ansi -> 8bitStr/(AnsiStr) ??
            elif valuetype == "Ansi":
                if forceUpConv == True:
                    _t = value.replace("#ansi.","",1)
                    ansiint = int(_t.rstrip("m")) if _t.endswith("m") else int(_t)
                    if ground == None or ground == "":
                        ground_ = "f" if ansiint in self.ansi_fgs else "b"
                    else:
                        ground_ = ground
                    eightbit = self.ansi_to_closest_eightbit( ansiint, ground_ )
                    if eightbit == None:
                        return self.ansi_num_to_str(ansiint)
                    return self.eightbit_num_to_str(eightbit)
                else:
                    return self.ansi_common_to_str(value)
            # RGBa -> 8bitStr,(alpha_notation)
        elif self.terminal.color_system == self.terminal.COLOR_SYSTEMS["standard"]:  # STANDARD
            # RGB  -> AnsiStr
            if valuetype == "RGB":
                return self.ansi_num_to_str(self.eightbit_to_closest_ansi(self.rgb_to_closest_eightbit(parsed.split(",")),ground))
            # 8bit -> AnsiStr
            elif valuetype == "8bit":
                return self.ansi_num_to_str(self.eightbit_to_closest_ansi(int(parsed),ground))
            # Ansi -> AnsiStr
            elif valuetype == "Ansi":
                return self.ansi_common_to_str(value)
            # RGBa -> 8bit,(alpha_notation)
        elif self.terminal.color_system == self.terminal.COLOR_SYSTEMS["windows"]:  # WINDOWS
            # RGB  -> AnsiStr
            if valuetype == "RGB":
                # Calling justFixWindows if on legacyWindows else fallback
                self.colorama_justfix()
                return self.ansi_num_to_str(self.eightbit_to_closest_ansi(self.rgb_to_closest_eightbit(parsed.split(",")),ground))
            # 8bit -> AnsiStr
            elif valuetype == "8bit":
                # Calling justFixWindows if on legacyWindows else fallback
                self.colorama_justfix()
                return self.ansi_num_to_str(self.eightbit_to_closest_ansi(int(parsed),ground))
            # Ansi -> AnsiStr
            elif valuetype == "Ansi":
                # Calling justFixWindows if on legacyWindows else fallback
                self.colorama_justfix()
                return self.ansi_common_to_str(value)
            # RGBa -> 8bit,(alpha_notation)

        # Return
        if value == None:
            # Unicode
            if tag.startswith("u."):
                try:
                    # Strip the "u." prefix and convert remaining hex to int
                    unicode_char = chr(int(tag[2:], 16))
                    return unicode_char.encode("utf-8").decode(self.terminal.encoding,errors=self.unicodeCharErrorMode)
                except ValueError:
                    return '{' + tag + '}'
            return '{'+tag+'}'
        return value

    def parse(self,inputStr:str,skipPalette:bool=False,forceUpConv:bool=False,handleSafely:bool=True,stripNonToken:bool=False) -> Union[str,tuple]:
        """If opacity is disabled returns the output-string, else returns a tuple with two values,
        the first is the output-string and the second a dictionary with index-sections mapped to their opacity.\n
        Example: 'hello' but the l:s are 0.5 opacity. -> ("hello", {"__om__":"0-1", "2-3":0.5})\n
        The '__om__' key just contains if opacity values from 0-1 or 0-255 are selected."""

        # Extract Tags
        tags = self.tag_extractor(inputStr)

        # Replace tags
        for tag in tags:
            try:
                newValue = self.get_tag_value(tag,skipPalette,forceUpConv,stripNonToken)
            except Exception as e:
                if handleSafely == True:
                    newValue = '{'+tag+'}'
                else:
                    raise
            inputStr = inputStr.replace('{'+tag+'}',newValue)

        # Replace tokens
        tags_tokens = self.filter_tokens(self.terminal.encoding,replace=False,_retCoded=False,asciiOnly=self.terminal.ascii_only)
        for token in tags_tokens.keys():
            if '{'+token+'}' in inputStr:
                inputStr = inputStr.replace('{'+token+'}',tags_tokens[token])

        # Return
        return inputStr
#endregion [fuse.include: ./formatting.py]
#region [fuse.include: ./console.py]
#fuse:imports
import shutil, sys, os
from typing import (
    Literal,
    Optional,
    Mapping,
    Union,
    Tuple
)
#fuse:imports


class Console():
    def __init__(
        self,
        useRich:Literal["auto","on","off",True,False]="auto",

        terminalPropertiesHandler=None,
        winTryEnaAnsiCol:Optional[bool]=False,

        stdin=None,
        stdout=None,
        stderr=None,

        printer=None,
        prompter=None,

        silentWinError:bool = False,

        rich_autoImport:bool = False,
        couple_rich_stdout:bool = False,
        color_system: Optional[
            Literal["auto", "standard", "256", "truecolor", "windows"]
        ] = "auto",
        force_terminal: Optional[bool] = None,
        force_jupyter: Optional[bool] = None,
        force_interactive: Optional[bool] = None,
        no_color: Optional[bool] = None,
        rich_emoji: bool = True,
        rich_emoji_variant: Optional[Literal["emoji", "text"]] = None,
        legacy_windows: Optional[bool] = None,
        win32_handle: Optional[int] = STDOUT,
        _environ: Optional[Mapping[str, str]] = None,
        terminal_default_size = (80,25),

        conResize_macFallback: Literal["ansi","applescript","curses"] = "ansi",
        conResize_linuxFallback: Literal["ansi","curses"] = "ansi",

        formatter_enableAlpha:bool = False,
        formatter_opacityFormat:str = "dec"

    ):

        self.silentWinError = silentWinError

        self.conResize_macFallback = conResize_macFallback
        self.conResize_linuxFallback = conResize_linuxFallback        

        # Stds
        self.selected_stdin = stdin if stdin != None else sys.stdin
        self.selected_stdout = stdout if stdout != None else sys.stdout
        self.selected_stderr = stderr if stderr != None else sys.stderr

        # PnP
        def _printer(inputstr,end="\n"):
            self.selected_stdout.write(inputstr+end)
            self.selected_stdout.flush()
        _prompter = input
        self.printer = printer if printer != None else _printer
        self.prompter = prompter if prompter != None else _prompter

        # Should use rich?
        if useRich == "auto" or (useRich == "on" or useRich == True):
            try:
                import rich
                self.useRich = True
            except:
                if rich_autoImport == True:
                    self.useRich = True
                else:
                    if useRich == "auto":
                        self.useRich = False
                    else:
                        raise
        else:
            self.useRich = False
        
        # Init
        if terminalPropertiesHandler != None and isinstance(terminalPropertiesHandler,TerminalBaseClass):
            self.terminal = terminalPropertiesHandler
        else:
            if self.useRich == True:
                self.terminal = TerminalProperties_richDependent(
                    parent=self,

                    stdin=self.selected_stdin,
                    stdout=self.selected_stdout,
                    stderr=self.selected_stderr,
                    printer=self.printer,

                    autoGetRich=rich_autoImport,
                    couple_rich_stdout= couple_rich_stdout,

                    color_system= color_system,
                    force_terminal= force_terminal,
                    force_jupyter= force_jupyter,
                    force_interactive= force_interactive,
                    no_color= no_color,
                    rich_emoji= rich_emoji,
                    rich_emoji_variant= rich_emoji_variant,
                    legacy_windows= legacy_windows,
                    win32_handle= win32_handle,

                    _environ=_environ,
                    terminal_default_size=terminal_default_size
                )
            else:
                self.terminal = TerminalProperties_nonRichDependent(
                    parent=self,

                    stdin=self.selected_stdin,
                    stdout=self.selected_stdout,
                    stderr=self.selected_stderr,
                    printer=self.printer,

                    color_system= color_system,
                    force_terminal= force_terminal,
                    force_jupyter= force_jupyter,
                    force_interactive= force_interactive,
                    no_color= no_color,
                    legacy_windows= legacy_windows,
                    win32_handle= win32_handle,

                    _environ=_environ,
                    terminal_default_size=terminal_default_size
                )

        self.platform = self.terminal.platform
        self.encoding = self.terminal.encoding
        self.importa_instance = self.terminal.importa_instance

        self.formatter = Text(self.terminal,formatter_enableAlpha,formatter_opacityFormat)

        # fix windows ansi
        if winTryEnaAnsiCol == True:
            os.system("")

    @property
    def stdin_isatty(self) -> Union[bool,None]:
        try:
            return self.selected_stdin.isatty()
        except AttributeError:
            return None
    @property
    def stdout_isatty(self) -> Union[bool,None]:
        try:
            return self.selected_stdout.isatty()
        except AttributeError:
            return None
    @property
    def stderr_isatty(self) -> Union[bool,None]:
        try:
            return self.selected_stderr.isatty()
        except AttributeError:
            return None

    def write_flusing_to_selstdout(self,towrite):
        self.selected_stdout.write(towrite)
        self.selected_stdout.flush()

    def set_console_title(self,title:str) -> bool:
        if title != None:
            # Windows
            if self.platform == "Windows":
                try:
                    subprocess.run(['title', title], shell=True, check=True)
                except subprocess.CalledProcessError:
                    if self.terminal.win32_lwt_avaliable == True:
                        try:
                            self.terminal._win32_lwt.set_title(title)
                            return True
                        except:
                            return False
                    if self.stdout_isatty == True:
                        self.selected_stdout.write(f"\x1b]2;{title}\x07")
                        self.selected_stdout.flush()
                    else:
                        return False
            else:
                if self.stdout_isatty == True:
                    # Linux
                    if self.platform == "Linux":
                        self.selected_stdout.write(f"\x1b]2;{title}\x07")
                        self.selected_stdout.flush()
                    # Mac/Darwin
                    elif self.platform == "Darwin":
                        self.selected_stdout.write(f"\x1b]2;{title}\x07")
                        self.selected_stdout.flush()
                    # Other
                    else:
                        raise OperationUnsupportedOnTerminal()
                else:
                    return False

            return True
        else:
            return False

    def get_console_title(self) -> Union[str,None]:
        # Windows
        if self.platform == "Windows":
            return _get_console_title_windows_cuzbuf()
        else:
            raise OperationUnsupportedOnTerminal()

    def get_console_size(self,fallback:Tuple[int,int]=None,cachePath=None,ask=True,_asker=None,_printer=None,cacheEncoding="utf-8") -> Tuple[int,int]:
        try:
            w,h = shutil.get_terminal_size((-1,-1))
        except:
            if self.terminal.win32_avaliable == True:
                _t = self.terminal._win32_lwt.screen_size
                w,h = _t.col,_t.row
                del _t
        # EC
        if (w == None or w == -1) or (h == None or h == -1):
            if cachePath != None:
                cacheValue_raw = None
                cacheValue = None
                inp_value = None
                _encoding = cacheEncoding if cacheEncoding != None else self.encoding
                # check path
                if cachePath == str:
                    cacheType = "path"
                    if os.path.exists(cachePath):
                        with open(cachePath,'r',encoding=_encoding).read() as file:
                            cacheValue_raw = file.read()
                            file.close()
                else:
                    cacheType = "stream"
                    cacheValue_raw = cachePath.read()
                # parse
                if cacheValue_raw != None:
                    try:
                        cacheValue = tuple([int(x) for x in cacheValue_raw.strip().split(",")])
                    except: pass

                if cacheValue == None:
                    if _asker == None:
                        _asker = self.prompter
                    if _printer == None:
                        _printer = self.printer

                    if ask == True:
                        _printer("Couldn't get consize, want to set it? [<width:int>,<height:int>]")
                        _printer(f"Will save to: {cachePath}")
                        _printer(f"If not press enter to use defaults: {fallback[0],fallback[1]}")
                        valid = False
                        while valid != True:
                            inp = _asker("<w>,<h>: ")
                            if inp.strip() == "":
                                inp_value = fallback
                                valid = True
                            else:
                                try:
                                    inp_value = tuple([int(x) for x in inp.strip().split(",")])
                                    valid = True
                                except: pass
                    else:
                        inp_value = fallback
                    
                    w,h = inp_value

                    # write
                    if cacheType == "stream":
                        cachePath.write(f"{w},{h}")
                        cachePath.flush()
                    else:
                        if os.path.exists(cachePath):
                            try:
                                with open(cachePath,'w',encoding=_encoding) as file:
                                    file.write(f"{w},{h}")
                            except: pass
                    
                    return w,h
                
                else:
                    try:
                        cacheValue = tuple([int(x) for x in cacheValue_raw.strip().split(",")])
                        w,h = cacheValue
                    except:
                        w,h = fallback
                    return w,h

            return fallback
        else:
            return w,h
            
    def set_console_size_curses(self,width:int,height:int) -> bool:
        try:
            try: import curses
            except:
                os.system(f"{sys.executable} -m pip install curses")
                import curses
            try:
                stdscr = curses.initscr()
                curses.resizeterm(height, width)
            finally:
                curses.endwin()
            return True
        except:
            return False

    def _set_console_size_windows_usingRich(self,width, height, silentWinError=False) -> Union[bool,None]:
        import ctypes
        # Get handle to console window
        h_console = self.terminal.win32_handle
        # Get current console screen buffer info
        console_info = self.terminal.win32_console_screen_buffer_info_obj
        success = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h_console, ctypes.byref(console_info))
        if success:
            # Calculate new console size
            console_info.srWindow.Right = width
            console_info.srWindow.Bottom = height
            # Set new console window size
            success = ctypes.windll.kernel32.SetConsoleWindowInfo(h_console, True, ctypes.byref(console_info.srWindow))
            if success:
                # Set new console screen buffer size
                console_info.dwSize.X = width
                console_info.dwSize.Y = height
                success = ctypes.windll.kernel32.SetConsoleScreenBufferSize(h_console, ctypes.byref(console_info.dwSize))
                if success:
                    return True
        # If any operation fails, raise an exception
        if silentWinError != True:
            raise ctypes.WinError()
        else:
            return False

    def _set_console_size_windows_alternative(self,width, height, handle=None, silentWinError=False) -> Union[bool,None]:
        if handle == None or type(handle) != int:
            if self.terminal.win32_avaliable == True:
                handle = self.terminal.win32_handle_value
            else:
                handle = -11 #STDOUT
        import ctypes
        # Get handle to console window
        h_console = ctypes.windll.kernel32.GetStdHandle(handle)
        # Define structure for console screen buffer info
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                        ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]
        class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
            _fields_ = [("dwSize", COORD),
                        ("dwCursorPosition", COORD),
                        ("wAttributes", ctypes.c_ushort),
                        ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", COORD)]
        # Get current console screen buffer info
        console_info = CONSOLE_SCREEN_BUFFER_INFO()
        success = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h_console, ctypes.byref(console_info))
        if success:
            # Calculate new console size
            console_info.srWindow.Right = width
            console_info.srWindow.Bottom = height
            # Set new console window size
            success = ctypes.windll.kernel32.SetConsoleWindowInfo(h_console, True, ctypes.byref(console_info.srWindow))
            if success:
                # Set new console screen buffer size
                console_info.dwSize.X = width
                console_info.dwSize.Y = height
                success = ctypes.windll.kernel32.SetConsoleScreenBufferSize(h_console, ctypes.byref(console_info.dwSize))
                if success:
                    return True
        # If any operation fails, raise an exception
        if silentWinError != True:
            raise ctypes.WinError()
        else:
            return False

    def _set_console_size_wansi(self,width:int,height:int):
        if self.stdout_isatty == True:
            self.selected_stdout.write(f"\033[8;{height};{width}t")
            self.selected_stdout.flush()
        else:
            raise OperationUnsupportedOnTerminal()

    def _set_console_size_applescript(self,width:int,height:int,applic="Terminal"):
        # osascript -e "tell app \"Terminal\" to tell window 1
        # set b to bounds
        # set item 3 of b to (item 1 of b) + $1
        # set bounds to b
        # end"
        try:
            script = f'''
            tell app "{applic}"
              set number of rows of first window to {height}
              set number of columns of first window to {width}
            end
            '''
            subprocess.check_output(['osascript', '-e', script]).decode().strip()
        except Exception as e:
            raise OperationUnsupportedOnTerminal()

    def set_console_size(self,width:int,height:int, macFallback:Literal["ansi","applescript","curses"]=None, linuxFallback:Literal["ansi","curses"]=None) -> bool:
        # Windows
        if self.platform == "Windows":
            try:
                subprocess.run(f'mode con: cols={width} lines={height}', shell=True, check=True)
            except subprocess.CalledProcessError:
                if self.terminal.win32_avaliable == True:
                    return self._set_console_size_windows_usingRich(width,height,silentWinError=self.silentWinError)
                else:
                    return self._set_console_size_windows_alternative(width,height,silentWinError=self.silentWinError)

        else:
            if self.platform in ["Linux","Darwin"]:
                try:
                    _bin = subprocess.run(f'resize -s {height} {width}', shell=True, check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    # Mac
                    if self.platform == "Darwin":
                        if macFallback == None:
                            macFallback = self.conResize_macFallback
                        if macFallback == "ansi":
                            self._set_console_size_wansi(width,height)
                        elif macFallback == "applescript":
                            self._set_console_size_applescript(width,height)
                        elif macFallback == "curses":
                            self.set_console_size_curses(width,height)
                        else:
                            raise OperationUnsupportedOnTerminal
                    # Linux
                    if self.platform == "Linux":
                        if linuxFallback == None:
                            linuxFallback = self.conResize_linuxFallback
                        if linuxFallback == "anis":
                            self._set_console_size_wansi(width,height)
                        elif linuxFallback == "curses":
                            self.set_console_size_curses(width,height)
                        else:
                            raise OperationUnsupportedOnTerminal
            else:
                raise OperationUnsupportedOnTerminal() 
    
    def clear_console(self,home:bool=True):
        # Windows
        if self.platform == "Windows":
            platform_specific_command = "cls"
        # Linux / Darwin
        elif self.platform == "Linux" or self.platform == "Darwin":
            platform_specific_command = "clear"
        else:
            raise OperationUnsupportedOnTerminal()
        try:
            subprocess.run([platform_specific_command], shell=True, check=True)
            if home == True and self.terminal.is_dumb_terminal != True:
                self.selected_stdout.write( "\033[H" )

        except subprocess.CalledProcessError:
            if self.terminal.is_dumb_terminal != True:
                if home == True:
                    self.selected_stdout.write( "\033[2J\033[H" )
                else:
                    self.selected_stdout.write( "\033[2J" )
                self.selected_stdout.flush()
            else:
                raise OperationUnsupportedOnTerminal()

    def BELL(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\x07")
        else:
            raise OperationUnsupportedOnTerminal()
    def HOME(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\x1b[H")
        else:
            raise OperationUnsupportedOnTerminal()
    def ENABLE_ALT_SCREEN(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\x1b[?1049h")
        else:
            raise OperationUnsupportedOnTerminal()
    def DISABLE_ALT_SCREEN(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\x1b[?1049l")
        else:
            raise OperationUnsupportedOnTerminal()
    def SHOW_CURSOR(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\x1b[?25h")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    self.terminal._win32_lwt.show_cursor()
            raise OperationUnsupportedOnTerminal()
    def HIDE_CURSOR(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\x1b[?25l")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    self.terminal._win32_lwt.hide_cursor()
            raise OperationUnsupportedOnTerminal()
    def CURSOR_UP(self,amnt:int=0):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout(f"\x1b[{amnt}A")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    for _ in range(amnt):
                        self.terminal._win32_lwt.move_cursor_up()
            raise OperationUnsupportedOnTerminal()
    def CURSOR_DOWN(self,amnt:int=0):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout(f"\x1b[{amnt}B")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    for _ in range(amnt):
                        self.terminal._win32_lwt.move_cursor_down()
            raise OperationUnsupportedOnTerminal()
    def CURSOR_FORWARD(self,amnt:int=0):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout(f"\x1b[{amnt}C")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    for _ in range(amnt):
                        self.terminal._win32_lwt.move_cursor_forward()
            raise OperationUnsupportedOnTerminal()
    def CURSOR_BACKWARD(self,amnt:int=0):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout(f"\x1b[{amnt}D")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    for _ in range(amnt):
                        self.terminal._win32_lwt.move_cursor_backward()
            raise OperationUnsupportedOnTerminal()
    def CURSOR_MOVE_TO_COLUMN(self,column:int=0):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout(f"\x1b[{column}G")
        else:
            if self.terminal.win32_lwt_avaliable == True:
                if self.platform == "Windows":
                    self.terminal._win32_lwt.move_cursor_to_column(column)
            raise OperationUnsupportedOnTerminal()
    def ERASE_IN_LINE(self,line:int=None):
        if line != None:
            if self.terminal.is_dumb_terminal != True:
                self.write_flusing_to_selstdout(f"\x1b[{line}K")
            else:
                if self.terminal.win32_lwt_avaliable == True:
                    if self.platform == "Windows":
                        self.terminal._win32_lwt.move_cursor_to(self.terminal.WindowsCoordinates(row=line-1, col=0))
                        self.terminal._win32_lwt.erase_line()
                raise OperationUnsupportedOnTerminal()
    def CURSOR_MOVE_TO(self,y:int=None,x:int=None):
        if x != None and y != None:
            if self.terminal.is_dumb_terminal != True:
                self.write_flusing_to_selstdout(f"\x1b[{y+1};{x+1}H")
            else:
                if self.terminal.win32_lwt_avaliable == True:
                    if self.platform == "Windows":
                        self.terminal._win32_lwt.move_cursor_to(self.terminal.WindowsCoordinates(row=y-1, col=x-1))
                raise OperationUnsupportedOnTerminal()
    def CURSOR_SAVE(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\033[s")
    def CURSOR_LOAD(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\033[u")

    def saveN0(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\033[s\033[0;0H")
    def loadN0(self):
        if self.terminal.is_dumb_terminal != True:
            self.write_flusing_to_selstdout("\033[0;0H\033[u")

    def swapp_ansi_ground(self,ansicode:str,strip:bool=False):
        _swapp_mapping = {
            "0": "0",
            "30": "40",
            "31": "41",
            "32": "42",
            "33": "43",
            "34": "44",
            "35": "45",
            "36": "46",
            "37": "47",
            "90": "100",
            "91": "101",
            "92": "102",
            "93": "103",
            "94": "104",
            "95": "105",
            "96": "106",
            "97": "107",
        }
        swapp_mapping = _swapp_mapping.copy()
        for key,value in _swapp_mapping.items():
            swapp_mapping[value] = key
        # Find
        ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])') # Define a regular expression pattern to match ANSI escape codes
        matches = ansi_escape_pattern.finditer(ansicode)                           # Use re.finditer to find all matches in the input string
        # Replace
        for match in matches:
            code = str(match.group())
            ocode = code
            if "38;2" in code or "48;2" in code:
                # replace rgb
                code = code.replace("48;2","§rgb-swapp§")
                code = code.replace("38;2","48;2")
                code = code.replace("§rgb-swapp§","38;2")
            else:
                if len(code) == 8 or len(code) == 9:
                    code = swapp_mapping[code]
            if strip == True:
                ansicode = ansicode.replace(ocode,"",1)
            else:
                ansicode = ansicode.replace(ocode,code,1)
        return ansicode

    def ensure_ansi_foreground(self,ansicode:str,strip:bool=False):
        swapp_mapping_fg_to_bg = {
            "0": "0",
            "30": "40",
            "31": "41",
            "32": "42",
            "33": "43",
            "34": "44",
            "35": "45",
            "36": "46",
            "37": "47",
            "90": "100",
            "91": "101",
            "92": "102",
            "93": "103",
            "94": "104",
            "95": "105",
            "96": "106",
            "97": "107",
        }
        swapp_mapping_bg_to_fg = {}
        for key,value in swapp_mapping_fg_to_bg.items():
            swapp_mapping_bg_to_fg[value] = key
        # Find
        ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])') # Define a regular expression pattern to match ANSI escape codes
        matches = ansi_escape_pattern.finditer(ansicode)                           # Use re.finditer to find all matches in the input string
        # Replace
        for match in matches:
            code = str(match.group())
            ocode = code
            if "48;2" in code:
                # replace rgb
                code = code.replace("48;2","38;2")
            else:
                #if len(code) == 8 or len(code) == 9:
                #    if code in list(swapp_mapping_bg_to_fg.keys()):
                #        code = swapp_mapping_bg_to_fg[code]
                shortcode = code.lstrip("\033[").rstrip("m")
                if shortcode in list(swapp_mapping_bg_to_fg.keys()):
                    code = "\033["+swapp_mapping_bg_to_fg[shortcode]+"m"
            if strip == True:
                ansicode = ansicode.replace(ocode,"",1)
            else:
                ansicode = ansicode.replace(ocode,code,1)
        return ansicode

    def ensure_ansi_background(self,ansicode:str,strip:bool=False):
        swapp_mapping_fg_to_bg = {
            "0": "0",
            "30": "40",
            "31": "41",
            "32": "42",
            "33": "43",
            "34": "44",
            "35": "45",
            "36": "46",
            "37": "47",
            "90": "100",
            "91": "101",
            "92": "102",
            "93": "103",
            "94": "104",
            "95": "105",
            "96": "106",
            "97": "107",
        }
        # Find
        ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])') # Define a regular expression pattern to match ANSI escape codes
        matches = ansi_escape_pattern.finditer(ansicode)                           # Use re.finditer to find all matches in the input string
        # Replace
        for match in matches:
            code = str(match.group())
            ocode = code
            if "38;2" in code:
                # replace rgb
                code = code.replace("38;2","48;2")
            else:
                #if len(code) == 8 or len(code) == 9:
                #    if code in list(swapp_mapping_fg_to_bg.keys()):
                #        code = swapp_mapping_fg_to_bg[code]
                shortcode = code.lstrip("\033[").rstrip("m")
                if shortcode in list(swapp_mapping_fg_to_bg.keys()):
                    code = "\033["+swapp_mapping_fg_to_bg[shortcode]+"m"
            if strip == True:
                ansicode = ansicode.replace(ocode,"",1)
            else:
                ansicode = ansicode.replace(ocode,code,1)
        return ansicode

    def fill_terminal_buffering(
        self,
        char:str,
        savePos:bool=False,

        getConSize_fallback:Tuple[int,int]=None,
        getConSize_cachePath=None,
        getConSize_ask=True,
        getConSize_asker=None,
        getConSize_printer=None,
        getConSize_cacheEncoding="utf-8"
    ):
        if savePos == True: self.CURSOR_SAVE()
        w,h = self.get_console_size(
            fallback = getConSize_fallback,
            cachePath = getConSize_cachePath,
            ask = getConSize_ask,
            _asker = getConSize_asker,
            _printer = getConSize_printer,
            cacheEncoding = getConSize_cacheEncoding
        )
        self.CURSOR_MOVE_TO(0,0)
        self.write_flusing_to_selstdout( ( (round(w/len(removeAnsiSequences(char)))*char+"\n")*h ).rstrip("\n") )
        if savePos == True: self.CURSOR_LOAD()

    def fill_terminal_pos(
        self,
        char:str,
        savePos:bool=False,

        getConSize_fallback:Tuple[int,int]=None,
        getConSize_cachePath=None,
        getConSize_ask=True,
        getConSize_asker=None,
        getConSize_printer=None,
        getConSize_cacheEncoding="utf-8"
    ):
        if savePos == True: self.CURSOR_SAVE()
        w,h = self.get_console_size(
            fallback = getConSize_fallback,
            cachePath = getConSize_cachePath,
            ask = getConSize_ask,
            _asker = getConSize_asker,
            _printer = getConSize_printer,
            cacheEncoding = getConSize_cacheEncoding
        )
        line = round(w/len(removeAnsiSequences(char)))*char
        for y in range(h):
            self.CURSOR_MOVE_TO(y,0)
            self.write_flusing_to_selstdout(line)
        if savePos == True: self.CURSOR_LOAD()

    def write_at_pos(self,x:int,y:int,str:str,savePos:bool=False):
        if savePos == True: self.CURSOR_SAVE()
        self.CURSOR_MOVE_TO(y,x)
        self.write_flusing_to_selstdout(str)
        if savePos == True: self.CURSOR_LOAD()

    def input_at_pos(self,x:int,y:int,prompt:str="",savePos:bool=False) -> str:
        if savePos == True: self.CURSOR_SAVE()
        self.CURSOR_MOVE_TO(y,x)
        if savePos == True: self.CURSOR_LOAD()
        return self.prompter(prompt)


#endregion [fuse.include: ./console.py]
#region [fuse.include: ./tui.py]

#endregion [fuse.include: ./tui.py]