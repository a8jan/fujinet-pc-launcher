
import wx
import wx.adv
import sys
from pathlib import Path

from launcher.config import cfg
from launcher.logview import LogFrame
from launcher.procmgr import ProcessMgr, FujiNetMgr, NetSioMgr


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

        pen = wx.Pen('#606060')
        r = min(self.Size.width, self.Size.height)//3 - 1
        if self.active ^ self.transitioning:
            color = self.GetForegroundColour()
            # pen = wx.TRANSPARENT_PEN
            # r = min(self.Size.width, self.Size.height)//3
        else:    
            color = '#716c5d'
            # pen = wx.Pen('#606060')
            # r = min(self.Size.width, self.Size.height)//4
        # draw circle
        gc.SetPen(pen)
        gc.SetBrush(wx.Brush(color))
        gc.DrawCircle(self.Size.width//2, self.Size.height//2, r)

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


def scale_bitmap(bmp, factor):
    img = bmp.ConvertToImage().Scale(
        bmp.Width * factor,
        bmp.Height * factor, 
        wx.IMAGE_QUALITY_HIGH
    )
    return wx.Bitmap(img)


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

        wx.Frame.__init__(self)

        # if wx.Platform == '__WXMAC__':
        #     self.SetBackgroundStyle(wx.BG_STYLE_TRANSPARENT)
        # else:
        #     self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.Create(parent, wx.ID_ANY, "FujiNet-PC", 
            style=wx.FRAME_SHAPED | wx.SIMPLE_BORDER |
            # this allows to minimize shaped window by clicking its icon on task bar
            (wx.MINIMIZE_BOX if wx.Platform == '__WXMSW__' else 0))

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.stay_on_top = False
        self.delta = (0, 0)

        # GUI scale
        self.scale = cfg.gui_scale

        self.icons = wx.IconBundle(cfg.image_path("launcher-bg.ico"))
        if not self.icons.IsEmpty():
            self.SetIcons(self.icons)

        self.bmp = scale_bitmap(wx.Bitmap(cfg.image_path("fujinet-xl.png")), self.scale)
        bmp_size = self.bmp.GetSize()
        self.SetClientSize(bmp_size)

        self.mask_bmp = scale_bitmap(wx.Bitmap(cfg.image_path("fujinet-xl-mask.png")), self.scale)

        self.set_window_shape()

        # Log viewer window
        self.log_view = LogFrame(self, self)
        if not self.icons.IsEmpty():
            self.log_view.SetIcons(self.icons)

        def led_size():
            return int(32*self.scale), int(32*self.scale)

        def led_pos(x, y):
            w, h = led_size()
            return int(x*self.scale-w/2), int(y*self.scale-h/2)

        # LEDs
        # Power - on for running fujinet
        self.power_led = LedIndicator(self, pos=led_pos(54, 70), size=led_size())
        self.power_led.SetForegroundColour('#FFFFFF')
        self.set_power_led(False)
        # Wi-Fi - on for running netsiohub
        self.wifi_led = LedIndicator(self, pos=led_pos(116, 70), size=led_size())
        self.wifi_led.SetForegroundColour('#04DBFE')
        self.set_wifi_led(False)
        # SIO - on for command being processed
        self.sio_led = LedIndicator(self, pos=led_pos(268, 70), size=led_size())
        self.sio_led.SetForegroundColour('#FEA304')
        self.set_sio_led(False)

        # Buttons
        # Power
        self.quit_bnt = FnButton(self, label="Off", pos=(16*self.scale, 206*self.scale), size=(48, 24))
        self.quit_bnt.SetToolTip("Quit")
        self.quit_bnt.Bind(wx.EVT_BUTTON, self.on_quit)
        # SD card
        self.sd_bnt = FnButton(self, label="SD", pos=(bmp_size.width-16*self.scale-48, 206*self.scale), size=(48, 24))
        self.sd_bnt.SetToolTip("Open SD Card folder")
        self.sd_bnt.Bind(wx.EVT_BUTTON, lambda e: self.open_sd_folder())
        # # Button A
        # a_bnt = wx.Button(self, label="A", pos=(34, 12), size=(32, 32))
        # a_bnt.SetToolTip("TBD")
        # # Button B
        # b_bnt = wx.Button(self, label="B", pos=(88, 12), size=(32, 32))
        # b_bnt.SetToolTip("TBD")
        # Button C
        self.c_bnt = FnButton(self, label="Reset", pos=(bmp_size.width-16*self.scale-54, 14*self.scale), size=(54, 24))
        self.c_bnt.SetToolTip("Restart FujiNet")
        self.c_bnt.Bind(wx.EVT_BUTTON, lambda e: self.fujinet.restart_process())

        # some helper timers
        # alive timer
        self.alive_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_alive_timer, self.alive_timer)
        # shutdown timer
        self.shutdown_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_shutdown_timer, self.shutdown_timer)

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
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)

        # # focus evenet
        # self.Bind(wx.EVT_ACTIVATE, self.on_active)

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

        # start fujinet-pc and netsiohub proceses if configured to auto-start
        self.start_tasks()

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
        self.SetTransparent(255 if evt.Active else 192)
        self.Refresh()
        evt.Skip()

    def start_tasks(self):
        # start fujinet-pc process manager (thread)
        self.fujinet = FujiNetMgr(self.log_view.logger)
        self.fujinet.start()
        # start netsiohub process manager (thread)
        self.netsio = NetSioMgr(self.log_view.logger)
        self.netsio.start()
        # fujinet and netsio alive check
        self.alive_timer.Start(500)

        if cfg.netsio_autostart:
            # start netsio hub process
            self.netsio.start_process()

        if cfg.fujinet_autostart:
            # start fujinet-pc process
            if cfg.netsio_autostart:
                # wait a bit to start netsio hub
                wx.CallLater(200, self.fujinet.start_process)
            else:
                self.fujinet.start_process()

    def stop_tasks(self):
        self.alive_timer.Stop()
        # stop netsio
        if self.fujinet.is_running():
            # give fujinet-pc some time for gracefull shutdown
            # before shutting down netsio 
            wx.CallLater(600, self.netsio.shutdown)
        else:
            self.netsio.shutdown()
        # stop fujinet
        self.fujinet.shutdown()
        self.shutdown_timer.Start(1000)

    def on_alive_timer(self, evt):
        # check fujinet
        if not self.fujinet.is_alive():
            self.power_led.set(not self.power_led.get())
            self.power_led.SetToolTip("Lost control over FujiNet")
        elif self.fujinet.status() == ProcessMgr.STATUS_STOPPING:
            self.power_led.set(not self.power_led.get())
            self.power_led.SetToolTip("Stopping FujiNet")
        # check netsio
        if not self.netsio.is_alive():
            self.wifi_led.set(not self.wifi_led.get())
            self.wifi_led.SetToolTip("Lost control over NetSIO hub")
        elif self.netsio.status() == ProcessMgr.STATUS_STOPPING:
            self.wifi_led.set(not self.wifi_led.get())
            self.wifi_led.SetToolTip("Stopping NetSIO hub")

    def on_shutdown_timer(self, evt):
        if self.fujinet.is_alive() or self.netsio.is_alive():
            status = not self.power_led.get()
            self.power_led.set(status)
            self.wifi_led.set(status)
            self.sio_led.set(status)
        else:
            # self.fujinet.join()
            # self.netsio.join()
            self.good_bye()

    def on_quit(self, evt):
        self.Close()

    def on_close(self, evt):
        self.Iconize()
        self.sd_bnt.Disable()
        self.quit_bnt.Disable()
        self.c_bnt.Disable()
        self.stop_tasks()

    def good_bye(self):
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
        def status_str(proc_mgr: ProcessMgr):
            t = {
                ProcessMgr.STATUS_RUNNING: "running",
                ProcessMgr.STATUS_STOPPED: "stopped",
                ProcessMgr.STATUS_STOPPING: "stopping"
            }.get(proc_mgr.status(), "unknown")
            if not proc_mgr.is_alive():
                if t: t += ", "
                t += "no control"
            return " ({})".format(t) if t else ""

        menu = wx.Menu()
        menu_fn = wx.Menu()
        menu_hub = wx.Menu()

        menu_fn.Append(self.MENU_FN_RESTART, "Restart")
        menu_fn.AppendSeparator()
        menu_fn.Append(self.MENU_FN_START, "Start").Enable(self.fujinet.is_alive())
        menu_fn.Append(self.MENU_FN_STOP, "Stop").Enable(self.fujinet.is_alive())

        menu_hub.Append(self.MENU_HUB_RESTART, "Restart")
        menu_hub.AppendSeparator()
        menu_hub.Append(self.MENU_HUB_START, "Start").Enable(self.netsio.is_alive())
        menu_hub.Append(self.MENU_HUB_STOP, "Stop").Enable(self.netsio.is_alive())

        menu.Append(self.MENU_FN_WEBUI, "Open WebUI").Enable(self.fujinet.is_running())
        menu.Append(self.MENU_SD_OPEN, "Open SD Card folder")
        # menu.Append(self.MENU_SD_SET, "Select SD folder ...")
        menu.AppendSeparator()
        menu.AppendSubMenu(menu_fn, "FujiNet{}".format(status_str(self.fujinet)))
        menu.AppendSubMenu(menu_hub, "NetSIO hub{}".format(status_str(self.netsio)))
        menu.AppendSeparator()
        menu.Append(self.MENU_ON_TOP, "Stay on top", kind=wx.ITEM_CHECK).Check(self.stay_on_top)
        menu.Append(self.MENU_LOG_VIEW, "Show log")
        menu.Append(wx.ID_ABOUT, "About")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, "&Quit\tCtrl+Q")  # TODO make Ctrl+Q to quit
        return menu

    def on_menu_item(self, event):
        eid = event.GetId()
        if eid == self.MENU_FN_WEBUI:
            wx.LaunchDefaultBrowser(cfg.fujinet_webui)  # use BROWSER_NOBUSYCURSOR ?
        elif eid == self.MENU_FN_START:
            self.fujinet.start_process()
        elif eid == self.MENU_FN_STOP:
            self.fujinet.stop_process()
        elif eid == self.MENU_FN_RESTART:
            if not self.fujinet.is_alive():
                # recovery from control thread death
                self.fujinet = FujiNetMgr(self.log_view.logger)
                self.fujinet.start()
            self.fujinet.restart_process()
        elif eid == self.MENU_HUB_START:
            self.netsio.start_process()
        elif eid == self.MENU_HUB_STOP:
            self.netsio.stop_process()
        elif eid == self.MENU_HUB_RESTART:
            if not self.netsio.is_alive():
                # recovery from control thread death
                self.netsio = NetSioMgr(self.log_view.logger)
                self.netsio.start()
            self.netsio.restart_process()
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
        wx.LaunchDefaultBrowser('file:{}'.format(cfg.fujinet_SD_path))

    def select_sd_folder(self):
        new_sd_dir = wx.DirSelector("Choose SD folder", cfg.fujinet_SD_path)
        if new_sd_dir.strip():
            print("new SD", new_sd_dir)

    def show_about(self):
        info = wx.adv.AboutDialogInfo()
        # fname = os.path.join(os.path.dirname(sys.argv[0]), "img", "alien48.png")
        icons = wx.IconBundle(cfg.image_path("launcher.ico"))
        if not icons.IsEmpty():
            info.SetIcon(icons.GetIcon(64))
        # info.SetName(version.NAME)
        info.SetName("FujiNet-PC Launcher")
        # info.SetVersion(version.VERSION)
        info.SetVersion("0.1")
        # info.SetDescription(version.DESC)
        info.SetDescription("This launcher program controls FujiNet-PC and NetSIO hub.\n\n"
        "FujiNet-PC is a port of #FujiNet firmware to Linux, macOS and Windows.\n\n"
        "NetSIO hub is a complementary program to bridge a communication between\n"
        "FujiNet or FujiNet-PC and Atari 8-bit computer emulator like Altirra.\n\n"
        )
        info.SetCopyright('(C) 2022 apc')
        info.SetWebSite('https://fujinet.online/')
        # info.SetLicence(license)
        # info.AddDeveloper("Jan Krupa")
        wx.adv.AboutBox(info, self)

    def show_log(self):
        if self.log_view is None:
            self.log_view = LogFrame(self, self)
            if not self.icons.IsEmpty():
                self.log_view.SetIcons(self.icons)
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
        
def main():
    print("__file__:", __file__)
    print("sys.executable:", sys.executable)
    print("sys.version:", sys.version)
    print("sys.path:")
    print("\n".join(sys.path))
    print("sys.argv", sys.argv)

    app = MyApp()
    app.MainLoop()
