import platform
import sys
import os.path
import argparse
from typing import AnyStr

# FujiNet API and WebUI
FN_WEB_HOST : str = "localhost"
FN_WEB_PORT : int = 8000
# Local TCP port Altirra custom device is available
NETSIO_ATDEV_PORT : int = 9996
# UDP port NetSIO is accepting messages from peripherals
NETSIO_PORT : int = 9997



def to_port(s) -> int:
    try:
        port = int(s)
        if 0 >= port or 65536 <= port:
            raise ValueError
    except (ValueError, TypeError):
        print("Invalid port number:", s)
        port = None
    return port


class Config:
    def __init__(self) -> None:
        # print version and exit
        self.print_version: bool = False

        # GUI scale
        self.gui_scale : float = 0.6
        # Window will stay on top of other windows
        self.stay_on_top: bool = False

        # # parsed command line arguments
        # self.args : argparse.Namespace = None

        # auto-start options
        self.fujinet_autostart : bool = True
        self.netsio_autostart : bool = True

        # data directory (writable user files)
        self.launcher_dir : AnyStr = os.path.dirname(sys.argv[0])
        # runtime directory (provided by pyinstaller or appimage, can be read-only)
        self.launcher_rundir : AnyStr = os.path.dirname(__file__)

        # fujinet-pc working directory (with data, web, fonts, etc.)
        self.fujinet_rundir : AnyStr = os.path.join(
            os.path.dirname(self.launcher_dir), # TODO use launcher_rundir for appimage
            "fujinet-pc"
        )
        # full path to fujinet-pc executable
        self.fujinet_path : AnyStr = os.path.join(
            self.fujinet_rundir,
            "fujinet.exe" if platform.system().lower() == "windows" else "fujinet"
        )
        # fujinet-pc user data directory (with fnconfig.ini file and SD card)
        self.fujinet_dir : AnyStr = os.path.join(
            os.path.dirname(self.launcher_dir),
            "fujinet-pc"
        )

        # netsiohub working directory
        self.netsio_rundir : AnyStr = os.path.dirname(self.launcher_rundir)
        # module name
        self.netsio_module : str = "netsiohub"
        # auto-start NetSIO hub
        self.netsio_autostart : bool = True

        # Launcher label
        self.launcher_label : str = ""
        # path to FN configuration file
        self.fnconfig : AnyStr = "" # use default (fujinet-pc/fnconfig.ini)
        # path to SD "card" directory
        self.sd_path : AnyStr = "" # use default (fujinet-pc/SD)

        # FN WebUI and API URL's
        self.fujinet_webui_host : str = FN_WEB_HOST
        self.fujinet_webui_port : int = FN_WEB_PORT

        self.atdev_port: int = None
        self.netsio_port: int = None


    def image_path(self, fname):
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base = self.launcher_rundir
        return os.path.join(base, "images", fname)

    def print_dir_info(self):
        print("launcher dir:", self.launcher_dir)
        print("launcher rundir:", self.launcher_rundir)
        print("fujinet dir:", self.fujinet_dir)
        print("fujinet rundir:", self.fujinet_rundir)
        print("netsio rundir:", self.netsio_rundir)
        print("netsio module:", self.netsio_module)

    @property
    def fujinet_base_url(self) -> str:
        """URL to send requests to"""
        return "http://{}:{}".format(
            FN_WEB_HOST if self.fujinet_webui_host is None else self.fujinet_webui_host,
            FN_WEB_PORT if self.fujinet_webui_port is None else self.fujinet_webui_port
        )

    @property
    def fujinet_listen_url(self) -> str:
        """URL to listen for requests"""
        if self.fujinet_webui_host is None and self.fujinet_webui_port is None:
            return None # don't use -u url to start fujinet
        # run fujinet with -u http://host:port
        return "http://{}:{}".format(
            "0.0.0.0" if self.fujinet_webui_host is None else self.fujinet_webui_host,
            FN_WEB_PORT if self.fujinet_webui_port is None else self.fujinet_webui_port
        )

    @property
    def fujinet_sd_folder(self) -> AnyStr:
        """return specified SD path, if set, or default SD path"""
        return self.sd_path if self.sd_path else os.path.join(self.fujinet_dir, "SD")

    @property
    def fujinet_webui(self) -> str:
        return self.fujinet_base_url
    @property
    def fujinet_api_exit(self) -> str:
        return self.fujinet_base_url + "/restart?exit=1"
    @property
    def fujinet_api_swap(self) -> str:
        return self.fujinet_base_url + "/swap"


    def parse_args(self) -> None:
        arg_parser = argparse.ArgumentParser(description = 
                "This launcher program controls FujiNet-PC and NetSIO hub")
        arg_parser.add_argument('-l', '--label', type=str, help='Launcher label')
        arg_parser.add_argument('-g', '--gui-scale', type=float, help='GUI scale')
        arg_parser.add_argument('-t', '--top-window', dest='stay_on_top', action='store_true', help='Stay on top window')
        arg_parser.add_argument('-u', '--url', type=str, help='FujiNet web interface ([0.0.0.0][:8000])')
        arg_parser.add_argument('-c', '--fnconfig', help='Path to FujiNet configuration file (fnconfig.ini)')
        arg_parser.add_argument('-s', '--sd', type=str, help='Path to SD directory (SD)')
        arg_parser.add_argument('-p', '--port', type=int, help='TCP port used by Altirra NetSIO custom device (9996)')
        arg_parser.add_argument('-r', '--netsio-port', type=int, help='UDP port used by NetSIO peripherals (9997)')
        arg_parser.add_argument('--nohub', dest='nohub', action='store_true', help='Do not start NetSIO hub automatically')
        # -i N is shortcut for -l FujiNet-N -u localhost:8000+N -c FujiNet-N/fnconfig.ini -s FujiNet-N/SD -r 9000+N -p 10000+N"
        arg_parser.add_argument('-i', '--instance', type=int, help="FujiNet instance ID")
        arg_parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Log emulation device commands')
        arg_parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='Print debug output')
        arg_parser.add_argument('-V', '--version', dest='print_version', action='store_true', help='Print program version and exit')
        args = arg_parser.parse_args()

        # alter configuration
        if args.instance is not None:
            if 1 <= args.instance <= 999:
                name = "FujiNet-{}".format(args.instance)
                self.launcher_label = name
                print("label:", self.launcher_label)
                self.fnconfig = os.path.join(os.path.dirname(self.launcher_dir), name, "fnconfig.ini")
                print("fnconfig:", self.fnconfig)
                self.sd_path = os.path.join(os.path.dirname(self.launcher_dir), name, "SD")
                print("SD:", self.sd_path)
                self.fujinet_webui_host = "localhost"
                self.fujinet_webui_port = 8000+args.instance
                print("WebUI host:", self.fujinet_webui_host, "port:", self.fujinet_webui_port)
                self.netsio_port = 9000+args.instance
                print("NetSIO port:", self.netsio_port)
                self.atdev_port = 10000+args.instance
                print("AtDev port:", self.atdev_port)
            else:
                print("Instance number {} is out of range 1-999, ignoring".format(args.instance))

        if args.label is not None:
            self.launcher_label = args.label
            print("Label:", self.launcher_label)

        if args.gui_scale is not None:
            if args.gui_scale >= 0.3 and args.gui_scale <= 3.0:
                self.gui_scale = args.gui_scale
            print("GUI scale:", self.gui_scale)

        if args.stay_on_top is not None:
            self.stay_on_top = args.stay_on_top
            print("Stay on top:", self.stay_on_top)

        if args.fnconfig is not None:
            self.fnconfig = os.path.join(os.path.dirname(self.launcher_dir), args.fnconfig)
            print("fnconfig:", self.fnconfig)

        if args.sd is not None:
            self.sd_path = os.path.join(os.path.dirname(self.launcher_dir), args.sd)
            print("SD:", self.sd_path)

        if args.url is not None:
            host, port_str = args.url.split(':', 1) if ':' in args.url else (args.url, None)
            self.fujinet_webui_host = host or None
            self.fujinet_webui_port = to_port(port_str)
            print("WebUI host:", self.fujinet_webui_host, "port:", self.fujinet_webui_port)

        if args.nohub is not None:
            self.netsio_autostart = not args.nohub
            print("NetSIO hub auto-start:", self.netsio_autostart)

        if args.netsio_port is not None:
            self.netsio_port = to_port(args.netsio_port)
            print("NetSIO port:", self.netsio_port)

        if args.port is not None:
            self.atdev_port = to_port(args.port)
            print("AtDev port:", self.atdev_port)

        if args.print_version is not None:
            self.print_version = args.print_version


# global configuration
cfg = Config()
