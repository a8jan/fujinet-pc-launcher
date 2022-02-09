import wx


class LogFrame(wx.Frame):
    def __init__(self, parent, frame):
        wx.Frame.__init__(self, parent, -1, "FujiNet-PC Log",
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE) # | wx.FRAME_FLOAT_ON_PARENT)
        self.frame = frame
        self.panel = LogPanel(self, self)
        self.logger = Logger(self.panel.log_text, self.frame)

        # try to be HiDPI friendly
        w, h = self.GetTextExtent("MMMMMMMMMM")
        if w >= 240: f = 2.0
        elif w >= 180: f = 1.5
        elif w >= 150: f = 1.25
        else: f = 1.0
        self.SetClientSize((int(800*f),int(650*f)))
        self.SetMinClientSize((int(640*f), int(480*f)))

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        if evt.CanVeto():
            self.Hide()
            evt.Veto()
            return
        if self.frame is not None:
            self.frame.log_view = None
        self.Destroy()


class LogPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent)
        self.frame = frame
        self.log_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY)
        font = wx.Font()
        font.SetFamily(wx.FONTFAMILY_TELETYPE)
        font.SetPointSize(10)
        self.log_text.SetFont(font)
        self.log_text.SetBackgroundColour('#1E1E1E')
        self.log_text.SetForegroundColour('#C0C0C0')
        self.log_text.SetDefaultStyle(wx.TextAttr('#CFCFCF'))

        # hide_btn = wx.Button(self, label="Hide")
        # hide_btn.Bind(wx.EVT_BUTTON, self.on_hide_btn)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.log_text, 1, wx.ALL | wx.EXPAND)
        # vbox.Add(hide_btn, 0, wx.ALL | wx.ALIGN_CENTER, border=3)
        self.SetSizer(vbox)
        # self.SetBackgroundColour("red")

    def on_hide_btn(self, evt):
        self.frame.Hide()


class Logger:
    def __init__(self, log_text, window):
        self.log_text = log_text
        self.window = window

    def flush(self):
        pass

    def write(self, data):
        wx.CallAfter(self._write_after, data)

    def _write_after(self, data):
        # TODO pre-process input data
        self.log_text.AppendText(data)
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
