import wx

from launcher.config import cfg

from typing import Union


class Logger:
    def __init__(self, window: wx.Frame):
        self.window = window  # main window
        self.text_control: Union[wx.TextCtrl, None] = None  # text control to send log text
        self.buffer = ""
        self.flush_timer = wx.Timer(window)  # timer for text control updates
        window.Bind(wx.EVT_TIMER, self.on_flush_timer, self.flush_timer)

    def set_text_control(self, log_text: wx.TextCtrl):
        self.text_control = log_text
        self.flush()

    def flush(self):
        if self.text_control is not None:
            self.text_control.AppendText(self.buffer)
            self.buffer = ""
            # maintain text size at some level
            if self.text_control.GetLastPosition() > 1000000:
                self.text_control.Remove(0, 100000)

    def write(self, data: str):
        wx.CallAfter(self.append_buffer, data)

    def append_buffer(self, data: str):
        # process input text
        if "Running FujiNet" in data:
            self.window.set_power_led(True)
        elif "FujiNet stopped" in data or "FujiNet ended" in data:
            self.window.set_power_led(False)
        elif " > CF: " in data:
            self.window.set_sio_led(True)
        elif " > SIO CMD processed in " in data:
            self.window.set_sio_led(False)
        elif "Running NetSIO hub" in data:
            self.window.set_wifi_led(True)
        elif "NetSIO hub stopped" in data or "NetSIO hub ended" in data:
            self.window.set_wifi_led(False)
        # append text into buffer
        self.buffer += data
        # maintain buffer size at some level
        if len(self.buffer) > 1000000:
            self.buffer = self.buffer[100000:]
        # run timer to flush buffer
        if not self.flush_timer.IsRunning():
            self.flush_timer.StartOnce(250)

    def on_flush_timer(self, evt):
        self.flush()


class LogFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "{} log".format(cfg.launcher_label or "FujiNet-PC"),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE) # | wx.FRAME_FLOAT_ON_PARENT)
        self.panel = LogPanel(self)
        self.logger = None

        # try to be HiDPI friendly
        w, h = self.GetTextExtent("MMMMMMMMMM")
        if w >= 240: f = 2.0
        elif w >= 180: f = 1.5
        elif w >= 150: f = 1.25
        else: f = 1.0
        self.SetClientSize((int(800*f), int(650*f)))
        self.SetMinClientSize((int(640*f), int(480*f)))

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        # only hide, if possible
        if evt.CanVeto():
            self.Hide()
            evt.Veto()
            return
        self.reset_logger()
        self.Parent.log_view = None  # TODO better
        self.Destroy()

    def set_logger(self, logger: Logger):
        self.logger = logger
        logger.set_text_control(self.panel.log_text)

    def reset_logger(self):
        if self.logger is not None:
            self.logger.set_text_control(None)
            self.logger = None


class LogPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.log_text: wx.TextCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY)
        font = wx.Font()
        font.SetFamily(wx.FONTFAMILY_TELETYPE)
        font.SetPointSize(10)
        self.log_text.SetFont(font)
        self.log_text.SetBackgroundColour('#1E1E1E')
        self.log_text.SetForegroundColour('#E0E0E0')
        self.log_text.SetDefaultStyle(wx.TextAttr('#E0E0E0'))

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.log_text, 1, wx.ALL | wx.EXPAND)
        # vbox.Add(hide_btn, 0, wx.ALL | wx.ALIGN_CENTER, border=3)
        self.SetSizer(vbox)
        # self.SetBackgroundColour("red")
