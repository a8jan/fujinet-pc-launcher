#!/usr/bin/env python3


import wx
import wx.adv
import sys
import os
from pathlib import Path
from logview import LogFrame
from procmgr import FujiNetMgr


def ref_id():
    return wx.NewId()


try:  # Work around for wxpython prior to 4.0.2 where wx.NewIdRef first appeared
    TestId = wx.NewIdRef()
except AttributeError:
    wx.NewIdRef = ref_id


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
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.off_timer = wx.Timer(self)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        # self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)
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
        color = self.GetForegroundColour() if self.active ^ self.transitioning else '#d5d2ca'
        gc.SetBrush(wx.Brush(color))
        gc.DrawCircle(self.Size.width//2, self.Size.height//2, min(self.Size.width, self.Size.height)//4)

    # def on_erase(self, evt):
    #     pass

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


class FujiPanel(wx.Window):
    MENU_FN_WEBUI = wx.NewIdRef()
    MENU_FN_START = wx.NewIdRef()
    MENU_FN_STOP = wx.NewIdRef()
    MENU_FN_RESTART = wx.NewIdRef()
    MENU_HUB_START = wx.NewIdRef()
    MENU_HUB_STOP = wx.NewIdRef()
    MENU_HUB_RESTART = wx.NewIdRef()
    MENU_SD_OPEN = wx.NewIdRef()
    MENU_SD_SET = wx.NewIdRef()
    MENU_LOG_VIEW = wx.NewIdRef()
    MENU_ON_TOP = wx.NewIdRef()

    def __init__(self, parent, frame, bmp):
        wx.Window.__init__(self, parent)
        self.frame = frame
        self.bmp = bmp  # background bitmap
        bmp_size = self.bmp.GetSize()

        print("FujiPanel can set transparent:", self.CanSetTransparent())
        print("FujiPanel transparent bg:", self.IsTransparentBackgroundSupported())

        self.SetClientSize(bmp_size)

        # self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)

        # LEDs
        # Power
        self.power_led = LedIndicator(self, pos=(38, 54))
        self.power_led.SetForegroundColour('#FFFFFF')
        # Wi-Fi
        self.wifi_led = LedIndicator(self, pos=(100, 54))
        self.wifi_led.SetForegroundColour('#00A7FF')
        # SIO
        self.sio_led = LedIndicator(self, pos=(252, 54))
        self.sio_led.SetForegroundColour('#FF6262')

        # Buttons
        # Power
        quit_bnt = wx.Button(self, label="Off", pos=(16, 204), size=(48, 32))
        quit_bnt.SetToolTip("Quit")
        quit_bnt.Bind(wx.EVT_BUTTON, frame.on_exit)
        # SD card
        sd_bnt = wx.Button(self, label="SD", pos=(bmp_size.width-16-48, 204), size=(48, 32))
        sd_bnt.SetToolTip("Open SD folder")
        sd_bnt.Bind(wx.EVT_BUTTON, lambda e: self.open_sd_folder())

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
        self.Bind(wx.EVT_MENU, frame.on_exit, id=wx.ID_EXIT)

    # def on_paint(self, evt):
    #     dc = wx.PaintDC(self)
    #     gc = wx.GCDC(dc)
    #
    #     # dc.SetBrush(wx.TRANSPARENT_BRUSH)
    #     # gc.SetBrush(wx.TRANSPARENT_BRUSH)
    #     # gc.SetBackgroundMode(wx.TRANSPARENT)
    #     if wx.Platform in ['__WXGTK__', '__WXMSW__']:
    #         gc.SetBackground(wx.TRANSPARENT_BRUSH)
    #         gc.Clear()
    #
    # def on_erase(self, evt):
    #     pass

    def on_erase(self, evt):
        dc = evt.GetDC()
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        dc.DrawBitmap(self.bmp, 0, 0, True)

    def set_power_led(self, on: bool):
        self.power_led.set(on)

    def set_wifi_led(self, on: bool):
        self.wifi_led.set(on)

    def set_sio_led(self, on: bool):
        self.sio_led.set(on)

    def open_sd_folder(self):
        path = Path(sys.argv[0]).resolve().parent / "fujinet-pc" / "SD"
        wx.LaunchDefaultBrowser('file:{}'.format(path))

    def select_sd_folder(self):
        path = Path(sys.argv[0]).resolve().parent / "fujinet-pc" / "SD"
        new_sd_dir = wx.DirSelector("Choose SD folder", str(path))
        if new_sd_dir.strip():
            print("new SD", new_sd_dir)

    def on_right_down(self, evt):
        # create and show popup menu
        menu = self.create_popup_menu()
        self.PopupMenu(menu)
        menu.Destroy()

    def create_popup_menu(self):
        menu = wx.Menu()
        menu_fn = wx.Menu()
        menu_hub = wx.Menu()

        menu_fn.Append(self.MENU_FN_START, u"Start")
        menu_fn.Append(self.MENU_FN_STOP, u"Stop")
        menu_fn.Append(self.MENU_FN_RESTART, u"Restart")

        menu_hub.Append(self.MENU_HUB_START, u"Start")
        menu_hub.Append(self.MENU_HUB_STOP, u"Stop")
        menu_hub.Append(self.MENU_HUB_RESTART, u"Restart")

        menu.Append(self.MENU_FN_WEBUI, u"Open WebUI")
        menu.Append(self.MENU_SD_OPEN, u"Open SD folder")
        # menu.Append(self.MENU_SD_SET, u"Select SD folder ...")
        menu.AppendSubMenu(menu_fn, u"FujiNet")
        menu.AppendSubMenu(menu_hub, u"NetSIO hub")
        menu.Append(self.MENU_ON_TOP, u"Stay on top", kind=wx.ITEM_CHECK).Check(self.frame.stay_on_top)
        menu.Append(self.MENU_LOG_VIEW, u"View log")
        menu.AppendSeparator()
        menu.Append(wx.ID_ABOUT, u"About")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, u"&Quit\tCtrl+Q")
        return menu

    def on_menu_item(self, event):
        id = event.GetId()
        if id == self.MENU_FN_WEBUI:
            wx.LaunchDefaultBrowser('http://localhost:8000')  # use BROWSER_NOBUSYCURSOR ?
        elif id == self.MENU_FN_START:
            # self.frame.fujinet.start_process()
            pass
        elif id == self.MENU_FN_STOP:
            # self.frame.fujinet.stop_process()
            pass
        elif id == self.MENU_FN_RESTART:
            # self.frame.fujinet.restart_process()
            pass
        elif id == self.MENU_HUB_START:
            # self.frame.fujinet.start_process()
            pass
        elif id == self.MENU_HUB_STOP:
            # self.frame.fujinet.stop_process()
            pass
        elif id == self.MENU_HUB_RESTART:
            # self.frame.fujinet.restart_process()
            pass
        if id == self.MENU_SD_OPEN:
            self.open_sd_folder()
        elif id == self.MENU_SD_SET:
            self.select_sd_folder()
        elif id == self.MENU_LOG_VIEW:
            self.frame.show_log()
        elif id == self.MENU_ON_TOP:
            self.frame.toggle_stay_on_top()
        elif id == wx.ID_ABOUT:
            self.frame.show_about()


class TopFrame(wx.Frame):

    def __init__(self, parent):
        # wx.Frame.__init__(self, parent, wx.ID_ANY, "FujiNet-PC",
        #                   style=wx.FRAME_SHAPED | wx.SIMPLE_BORDER) # | wx.STAY_ON_TOP)
        wx.Frame.__init__(self)

        # self.SetBackgroundColour('#00ff00')
        # self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetBackgroundStyle(wx.BG_STYLE_TRANSPARENT)

        self.Create(parent, wx.ID_ANY, "FujiNet-PC",
                    style=wx.FRAME_SHAPED | wx.SIMPLE_BORDER) # | wx.STAY_ON_TOP)

        self.stay_on_top = False
        self.delta = (0, 0)

        print("TopFrame can set transparent:", self.CanSetTransparent())
        print("TopFrame transparent bg:", self.IsTransparentBackgroundSupported())

        fname = str(Path(sys.argv[0]).parent / "img" / "test.png")
        self.bmp = wx.Bitmap()
        self.bmp.LoadFile(fname, wx.BITMAP_TYPE_PNG)
        bmp_size = self.bmp.GetSize()
        self.SetClientSize(bmp_size)

        fname = str(Path(sys.argv[0]).parent / "img" / "test-mask.png")
        self.mask_bmp = wx.Bitmap()
        self.mask_bmp.LoadFile(fname, wx.BITMAP_TYPE_PNG)

        # panel = FujiPanel(self, self, self.bmp)
        # self.panel = panel

        # self.log_view = LogFrame(self, self)
        # self.log_view = None

        # sd_bnt = wx.Button(panel, label="SD", pos=(bmp_size.width-16-48, 204))
        # sd_bnt.SetToolTip("Open SD folder")
        # sd_bnt.SetBackgroundColour((56, 53, 53, 255))
        # sd_bnt.SetForegroundColour((250, 244, 5, 255))
        # sd_bnt.SetSize(48, 32)
        #
        # a_bnt = wx.Button(panel, label="A", pos=(40, 18))
        # a_bnt.SetToolTip("TODO")
        # a_bnt.SetBackgroundColour((56, 53, 53, 255))
        # a_bnt.SetForegroundColour((250, 244, 5, 255))
        # a_bnt.SetSize(32, 32)
        #
        # b_bnt = wx.Button(panel, label="B", pos=(94, 18))
        # b_bnt.SetToolTip("TODO")
        # b_bnt.SetBackgroundColour((56, 53, 53, 255))
        # b_bnt.SetForegroundColour((250, 244, 5, 255))
        # b_bnt.SetSize(32, 32)
        #
        # c_bnt = wx.Button(panel, label="C", pos=(254, 18))
        # c_bnt.SetToolTip("Restart FujiNet")
        # c_bnt.SetBackgroundColour((56, 53, 53, 255))
        # c_bnt.SetForegroundColour((250, 244, 5, 255))
        # c_bnt.SetSize(32, 32)
        #

        # panel.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)

        self.Bind(wx.EVT_PAINT, self.on_paint)

        # hot keys
        self.SetAcceleratorTable(wx.AcceleratorTable(
            [
                wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('Q'), wx.ID_EXIT),
            ]))

        # fname = os.path.join(os.path.dirname(sys.argv[0]), "img", "dragging.png")
        # self.cursorDragging = wx.Cursor(fname, wx.BITMAP_TYPE_PNG, 12, 8)

        # if wx.Platform != "__WXMAC__":
        #     # wxMac clips the tooltip to the window shape, YUCK!!!
        #     self.SetToolTipString("Right-click to close the window\n"
        #                           "Double-click the image to set/unset the window shape")

        if wx.Platform == "__WXGTK__":
            # wxGTK requires that the window be created before you can
            # set its shape, so delay the call to setWindowShape until
            # this event.
            self.Bind(wx.EVT_WINDOW_CREATE, self.set_window_shape)
        else:
            # On wxMSW and wxMac the window has already been created, so go for it.
            self.set_window_shape()

        # self.fujinet = FujiNetMgr(self.log_view.logger)
        # self.fujinet.start()
        # self.fujinet.start_process()

        # dc = wx.ClientDC(self)
        # dc.DrawBitmap(self.bmp, 0, 0, True)

    def set_window_shape(self, *evt):
        r = wx.Region(self.mask_bmp, (0, 0, 0), 0)
        # r = wx.Region(self.bmp, (0, 0, 0), 0)
        self.SetShape(r)

    def on_paint(self, evt):
        dc = wx.PaintDC(self)
        if wx.Platform == '__WXMSW__':
            dc.DrawBitmap(self.bmp, -1, -1, True)
        else:
            dc.DrawBitmap(self.bmp, 0, 0, True)
        # dc.SetBackground(wx.Brush('#ff0000'))
        # dc.Clear()

    def on_exit(self, evt):
        self.Iconize()
        # wx.CallAfter(self.fujinet.shutdown)  # TODO make non-blocking shutdown
        self.Close()

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

    def toggle_stay_on_top(self):
        self.stay_on_top = not self.stay_on_top
        style = self.GetWindowStyle()
        style = style | wx.STAY_ON_TOP if self.stay_on_top else style & ~wx.STAY_ON_TOP
        self.SetWindowStyle(style)

    def show_about(self):
        info = wx.adv.AboutDialogInfo()
        fname = os.path.join(os.path.dirname(sys.argv[0]), "img", "alien48.png")
        info.SetIcon(wx.Icon(fname, wx.BITMAP_TYPE_PNG))
        # info.SetName(version.NAME)
        info.SetName("FujiNet-PC Launcher")
        # info.SetVersion(version.VERSION)
        info.SetVersion("0.0")
        # info.SetDescription(version.DESC)
        info.SetDescription("FujiNet-PC Launcher is a wrapper to control FujiNet-PC and NetSIO hub programs.")
        info.SetCopyright('(C) 2021 apc')
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


class MyApp(wx.App):
    def OnInit(self):
        frame = TopFrame(None)
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        

app = MyApp()
app.MainLoop()
