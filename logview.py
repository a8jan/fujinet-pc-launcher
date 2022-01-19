import wx


class LogFrame(wx.Frame):
    def __init__(self, parent, frame):
        wx.Frame.__init__(self, parent, -1, "FujiNet-PC Log", size=(800, 650),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE) # | wx.FRAME_FLOAT_ON_PARENT)
        self.frame = frame
        self.panel = LogPanel(self, self)
        self.logger = Logger(self.panel.log_text, self.frame)

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
        self.log_text.SetFont(wx.Font(wx.FontInfo(10).Family(wx.TELETYPE)))
        self.log_text.SetBackgroundColour(wx.BLACK)
        self.log_text.SetForegroundColour(wx.WHITE)
        self.log_text.SetDefaultStyle(wx.TextAttr(wx.WHITE))

        hide_btn = wx.Button(self, label="Hide")
        hide_btn.Bind(wx.EVT_BUTTON, self.on_hide_btn)
        # self.Bind(wx.EVT_BUTTON, hide_btn, self.on_hide)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.log_text, 1, wx.ALL | wx.EXPAND)
        vbox.Add(hide_btn, 0, wx.ALL | wx.ALIGN_CENTER, border=3)
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
        if "Running fujinet" in data:
            self.window.set_power_led(True)
        elif "fujinet stopped" in data or "fujinet ended" in data:
            self.window.set_power_led(False)
        elif " > CF: " in data:
            self.window.set_sio_led(True)
        elif " > SIO CMD processed in " in data:
            self.window.set_sio_led(False)
