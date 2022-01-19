#!/usr/bin/env python3


import wx
import wx.adv
import sys

from pathlib import Path
from logview import LogFrame
from procmgr import FujiNetMgr


def new_id():
    return wx.NewIdRef()


# workaround for wxpython prior to 4.0.2 where wx.NewIdRef first appeared
try:
    TestId = new_id()
except AttributeError:
    new_id = wx.NewId


# workaround for DeprecationWarning: an integer is required (got type WindowIDRef)
if hasattr(wx._core, 'WindowIDRef'):
    wx._core.WindowIDRef.__index__ = wx._core.WindowIDRef.__int__


class LedIndicator(wx.Window):
    def __init__(self, parent, *args, **kwargs):
        if 'size' not in kwargs:
            kwargs['size'] = (32, 32)
        if 'style' not in kwargs:
            kwargs['style'] = wx.BORDER_NONE | wx.TRANSPARENT_WINDOW
        wx.Window.__init__(self, parent, *args, **kwargs)
        self.active = False
        self.transitioning = False
        self.SetForegroundColour('#FF0000')
        # self.SetBackgroundColour('#000000')
        self.off_timer = wx.Timer(self)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)
        self.Bind(wx.EVT_TIMER, self.on_timer)

    def on_paint(self, evt):
        dc = wx.PaintDC(self)
        gc = wx.GCDC(dc)

        # dc.SetBrush(wx.TRANSPARENT_BRUSH)
        # gc.SetBrush(wx.TRANSPARENT_BRUSH)
        # gc.SetBackgroundMode(wx.TRANSPARENT)
        if wx.Platform in ['__WXGTK__', '__WXMSW__']:
            gc.SetBackground(wx.TRANSPARENT_BRUSH)
            gc.Clear()

        gc.SetPen(wx.Pen('#606060'))
        color = self.GetForegroundColour() if self.active ^ self.transitioning else '#716c5d'
        gc.SetBrush(wx.Brush(color))
        gc.DrawCircle(self.Size.width//2, self.Size.height//2, min(self.Size.width, self.Size.height)//4)

    def on_erase(self, evt):
        pass

    def on_timer(self, evt):
        self.transitioning = False
        self.Refresh()

    def set(self, active=True):
        if self.active != active:
            self.active = active
            if active:
                if self.transitioning:
                    self.off_timer.Stop()
                    self.transitioning = False
                else:
                    self.Refresh()
            else:
                self.transitioning = True
                self.off_timer.StartOnce(50)

    def get(self):
        return self.active


class FnButton(wx.Button):
    def __init__(self, *args, **kwargs):
        if 'style' not in kwargs:
            kwargs['style'] = wx.NO_BORDER
        wx.Button.__init__(self, *args, **kwargs)
        self.bg_color = (56, 53, 53, 255)
        self.bg_color_hover = '#000'
        self.bg_color_active = '#a67301'
        self.SetBackgroundColour(self.bg_color)
        self.SetForegroundColour((250, 244, 5, 255))
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave)
        # self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

    def on_enter(self, evt):
        self.SetBackgroundColour(self.bg_color_hover)
        self.Refresh()

    def on_leave(self, evt):
        self.SetBackgroundColour(self.bg_color)
        self.Refresh()

    # def on_left_down(self, evt):
    #     self.SetBackgroundColour(self.bg_color_active)
    #     self.Refresh()
    #     evt.Skip()


class TopFrame(wx.Frame):

    MENU_FN_WEBUI = new_id()
    MENU_FN_START = new_id()
    MENU_FN_STOP = new_id()
    MENU_FN_RESTART = new_id()
    MENU_HUB_START = new_id()
    MENU_HUB_STOP = new_id()
    MENU_HUB_RESTART = new_id()
    MENU_SD_OPEN = new_id()
    MENU_SD_SET = new_id()
    MENU_LOG_VIEW = new_id()
    MENU_ON_TOP = new_id()

    def __init__(self, parent):
        # wx.Frame.__init__(self, parent, wx.ID_ANY, "FujiNet-PC",
        #                   style=wx.FRAME_SHAPED | wx.SIMPLE_BORDER) # | wx.STAY_ON_TOP)
        wx.Frame.__init__(self)

        # if wx.Platform == '__WXMAC__':
        #     self.SetBackgroundStyle(wx.BG_STYLE_TRANSPARENT)
        # else:
        #     self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.Create(parent, wx.ID_ANY, "FujiNet-PC",
                    style=wx.FRAME_SHAPED | wx.SIMPLE_BORDER)  # | wx.STAY_ON_TOP)

        # self.SetTransparent(128)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.stay_on_top = False
        self.delta = (0, 0)

        self.icons = wx.IconBundle("launcher.ico", type=wx.BITMAP_TYPE_ANY)
        if not self.icons.IsEmpty():
            self.SetIcons(self.icons)

        fname = str(Path(sys.argv[0]).parent / "img" / "fujinet-xl.png")
        self.bmp = wx.Bitmap()
        self.bmp.LoadFile(fname, wx.BITMAP_TYPE_PNG)
        bmp_size = self.bmp.GetSize()
        self.SetClientSize(bmp_size)

        fname = str(Path(sys.argv[0]).parent / "img" / "fujinet-xl-mask.png")
        self.mask_bmp = wx.Bitmap()
        self.mask_bmp.LoadFile(fname, wx.BITMAP_TYPE_PNG)

        self.set_window_shape()

        # Log viewer window
        self.log_view = LogFrame(self, self)

        # LEDs
        # Power - on for running fujinet
        self.power_led = LedIndicator(self, pos=(38, 54))
        self.power_led.SetForegroundColour('#FFFFFF')
        self.set_power_led(False)
        # Wi-Fi - on for running netsio-hub
        self.wifi_led = LedIndicator(self, pos=(100, 54))
        self.wifi_led.SetForegroundColour('#04DBFE')
        self.set_wifi_led(False)
        # SIO - on for command being processed
        self.sio_led = LedIndicator(self, pos=(252, 54))
        self.sio_led.SetForegroundColour('#FEA304')
        self.set_sio_led(False)

        # Buttons
        # Power
        quit_bnt = FnButton(self, label="Off", pos=(16, 206), size=(48, 24))
        quit_bnt.SetToolTip("Quit")
        quit_bnt.Bind(wx.EVT_BUTTON, self.on_exit)
        # SD card
        sd_bnt = FnButton(self, label="SD", pos=(bmp_size.width-16-48, 206), size=(48, 24))
        sd_bnt.SetToolTip("Open SD Card folder")
        sd_bnt.Bind(wx.EVT_BUTTON, lambda e: self.open_sd_folder())
        # # Button A
        # a_bnt = wx.Button(self, label="A", pos=(34, 12), size=(32, 32))
        # a_bnt.SetToolTip("TBD")
        # # Button B
        # b_bnt = wx.Button(self, label="B", pos=(88, 12), size=(32, 32))
        # b_bnt.SetToolTip("TBD")
        # Button C
        c_bnt = FnButton(self, label="Reset", pos=(248, 14), size=(54, 24))
        c_bnt.SetToolTip("Restart FujiNet")
        c_bnt.Bind(wx.EVT_BUTTON, lambda e: self.fujinet.restart_process())

        # Context menu
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_FN_WEBUI)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_FN_RESTART)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_LOG_VIEW)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_FN_START)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_FN_STOP)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_FN_RESTART)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_HUB_START)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_HUB_STOP)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_HUB_RESTART)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_ON_TOP)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_SD_OPEN)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=self.MENU_SD_SET)
        self.Bind(wx.EVT_MENU, self.on_menu_item, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)

        # focus evenets
        self.Bind(wx.EVT_SET_FOCUS, self.on_active)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_inactive)

        # window close event
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # panel.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)


        # # hot keys - does not work on mac and linux if there is no panel inside frame :(
        # self.SetAcceleratorTable(wx.AcceleratorTable(
        #     [
        #         wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('Q'), wx.ID_EXIT),
        #     ]))

        self.fujinet = FujiNetMgr(self.log_view.logger)
        self.fujinet.start()
        self.fujinet.start_process()

        # dc = wx.ClientDC(self)
        # dc.DrawBitmap(self.bmp, 0, 0, True)

    def set_window_shape(self, *evt):
        r = wx.Region(self.mask_bmp, (0, 0, 0), 0)
        self.SetShape(r)

    def on_paint(self, evt):
        dc = wx.PaintDC(self)
        if wx.Platform != '__WXMAC__':
            dc.SetBackground(wx.Brush('#C0C0C0'))
            dc.Clear()
        if wx.Platform == '__WXMSW__':
            dc.DrawBitmap(self.bmp, -1, -1, True)
        else:
            dc.DrawBitmap(self.bmp, 0, 0, True)

    def on_active(self, evt):
        print("active")
        # self.SetTransparent(255)
        # evt.Skip()

    def on_inactive(self, evt):
        print("inactive")
        # self.SetTransparent(128)
        # self.Refresh()
        # evt.Skip()

    def on_exit(self, evt):
        self.Close()

    def on_close(self, evt):
        # self.Iconize()
        self.fujinet.shutdown()  # TODO make non-blocking shutdown
        self.Destroy()

    def on_left_down(self, evt):
        self.CaptureMouse()
        origin_x, origin_y = self.GetPosition()
        x, y = self.ClientToScreen(evt.GetPosition())
        self.delta = (x - origin_x, y - origin_y)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        # self.SetCursor(self.cursorDragging)

    def on_left_up(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
            # self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def on_mouse_move(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            pos = evt.GetPosition()
            x, y = self.ClientToScreen(pos)
            self.Move((x - self.delta[0], y - self.delta[1]))

    def on_right_down(self, evt):
        # create and show popup menu
        menu = self.create_popup_menu()
        self.PopupMenu(menu)
        menu.Destroy()

    def create_popup_menu(self):
        menu = wx.Menu()
        menu_fn = wx.Menu()
        menu_hub = wx.Menu()

        menu_fn.Append(self.MENU_FN_RESTART, u"Restart")
        menu_fn.AppendSeparator()
        menu_fn.Append(self.MENU_FN_START, u"Start")
        menu_fn.Append(self.MENU_FN_STOP, u"Stop")

        menu_hub.Append(self.MENU_HUB_RESTART, u"Restart")
        menu_hub.AppendSeparator()
        menu_hub.Append(self.MENU_HUB_START, u"Start")
        menu_hub.Append(self.MENU_HUB_STOP, u"Stop")

        menu.Append(self.MENU_FN_WEBUI, u"Open WebUI")
        menu.Append(self.MENU_SD_OPEN, u"Open SD Card folder")
        # menu.Append(self.MENU_SD_SET, u"Select SD folder ...")
        menu.AppendSeparator()
        menu.AppendSubMenu(menu_fn, "FujiNet {}".format("(running)" if self.fujinet.is_running() else ""))
        menu.AppendSubMenu(menu_hub, u"NetSIO hub")
        menu.AppendSeparator()
        menu.Append(self.MENU_ON_TOP, u"Stay on top", kind=wx.ITEM_CHECK).Check(self.stay_on_top)
        menu.Append(self.MENU_LOG_VIEW, u"Log view")
        menu.Append(wx.ID_ABOUT, u"About")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, u"&Quit\tCtrl+Q")  # TODO make Ctrl+Q to quit
        return menu

    def on_menu_item(self, event):
        eid = event.GetId()
        if eid == self.MENU_FN_WEBUI:
            wx.LaunchDefaultBrowser('http://localhost:8000')  # use BROWSER_NOBUSYCURSOR ?
        elif eid == self.MENU_FN_START:
            self.fujinet.start_process()
        elif eid == self.MENU_FN_STOP:
            self.fujinet.stop_process()
        elif eid == self.MENU_FN_RESTART:
            self.fujinet.restart_process()
        elif eid == self.MENU_HUB_START:
            self.fujinet.start_process()
        elif eid == self.MENU_HUB_STOP:
            self.fujinet.stop_process()
        elif eid == self.MENU_HUB_RESTART:
            self.fujinet.restart_process()
        if eid == self.MENU_SD_OPEN:
            self.open_sd_folder()
        elif eid == self.MENU_SD_SET:
            self.select_sd_folder()
        elif eid == self.MENU_LOG_VIEW:
            self.show_log()
        elif eid == self.MENU_ON_TOP:
            self.toggle_stay_on_top()
        elif eid == wx.ID_ABOUT:
            self.show_about()

    def toggle_stay_on_top(self):
        self.stay_on_top = not self.stay_on_top
        style = self.GetWindowStyle()
        style = style | wx.STAY_ON_TOP if self.stay_on_top else style & ~wx.STAY_ON_TOP
        self.SetWindowStyle(style)

    def open_sd_folder(self):
        path = Path(sys.argv[0]).resolve().parent / "fujinet-pc" / "SD"
        wx.LaunchDefaultBrowser('file:{}'.format(path))

    def select_sd_folder(self):
        path = Path(sys.argv[0]).resolve().parent / "fujinet-pc" / "SD"
        new_sd_dir = wx.DirSelector("Choose SD folder", str(path))
        if new_sd_dir.strip():
            print("new SD", new_sd_dir)

    def show_about(self):
        info = wx.adv.AboutDialogInfo()
        # fname = os.path.join(os.path.dirname(sys.argv[0]), "img", "alien48.png")
        info.SetIcon(self.icons.GetIcon(64))
        # info.SetName(version.NAME)
        info.SetName("FujiNet-PC Launcher")
        # info.SetVersion(version.VERSION)
        info.SetVersion("0.0")
        # info.SetDescription(version.DESC)
        info.SetDescription("FujiNet-PC Launcher controls FujiNet-PC and NetSIO hub programs.")
        info.SetCopyright('(C) 2022 apc')
        # info.SetWebSite('http://www.zavreno.cz')
        # info.SetLicence(licence)
        # info.AddDeveloper('Jan Krupa')
        # info.AddDocWriter('Jan Krupa')
        # info.AddArtist('Unknow Artist')
        # info.AddTranslator('Unknown Translator')
        wx.adv.AboutBox(info, self)

    def show_log(self):
        if self.log_view is None:
            self.log_view = LogFrame(self, self)
        self.log_view.Show()
        self.log_view.Raise()

    def set_power_led(self, on: bool):
        self.power_led.set(on)
        self.power_led.SetToolTip("FujiNet is {}running".format("" if on else "not "))

    def set_wifi_led(self, on: bool):
        self.wifi_led.set(on)
        self.wifi_led.SetToolTip("NetSIO hub is {}running".format("" if on else "not "))

    def set_sio_led(self, on: bool):
        self.sio_led.set(on)


class MyApp(wx.App):
    def OnInit(self):
        frame = TopFrame(None)
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        

app = MyApp()
app.MainLoop()
