import platform
import sys
import os.path
from tempfile import gettempprefix

class Config:
    def __init__(self) -> None:
        # GUI scale
        self.gui_scale = 0.75

        # auto-start options
        self.fujinet_autostart = True
        self.netsio_autostart = True

        # data directory (writable user files)
        self.launcher_dir = os.path.dirname(sys.argv[0])
        # runtime directory (provided by pyinstaller or appimage, can be read-only)
        self.launcher_rundir = os.path.dirname(__file__)
        print("launcher dir:", self.launcher_dir)
        print("launcher rundir:", self.launcher_rundir)

        # fujinet-pc working directory (with data, web, fonts, etc.)
        self.fujinet_rundir = os.path.join(
            os.path.dirname(self.launcher_dir), # TODO use launcher_rundir for appimage
            "fujinet-pc"
        )
        # full path to fujinet-pc executable
        self.fujinet_path = os.path.join(
            self.fujinet_rundir,
            "fujinet.exe" if platform.system().lower() == "windows" else "fujinet"
        )
        # fujinet-pc user data directory (with fnconfig.ini file and SD card)
        self.fujinet_dir = os.path.join(
            os.path.dirname(self.launcher_dir),
            "fujinet-pc"
        )
        # virtual SD card
        self.fujinet_SD_path = os.path.join(self.fujinet_dir, "SD")

        print("fujinet dir:", self.fujinet_dir)
        print("fujinet rundir:", self.fujinet_rundir)

        # netsiohub working directory
        self.netsio_rundir = os.path.dirname(self.launcher_rundir)
        # module name
        self.netsio_module = "netsiohub"
        print("netsio rundir:", self.netsio_rundir)
        print("netsio module:", self.netsio_module)

        # fujinet WebUI and API URL's
        self.fujinet_webui_host = "localhost"
        self.fujinet_webui_port = 8000

        self.fujinet_webui = self.fujinet_base_url
        self.fujinet_api_exit = self.fujinet_base_url + "/restart?exit=1"

    def image_path(self, fname):
        return os.path.join(self.launcher_dir, "images", fname)

    @property
    def fujinet_base_url(self):
        """URL to send requests to"""
        return "http://{}:{}".format(
            "localhost" if self.fujinet_webui_host is None else self.fujinet_webui_host,
            8000 if self.fujinet_webui_port is None else self.fujinet_webui_port
        )

    @property
    def fujinet_listen_url(self):
        """URL to listen for requests"""
        if self.fujinet_webui_host is None and self.fujinet_webui_port is None:
            return None # don't use -u url to start fujinet
        # run fujinet with -u http://host:port
        return "http://{}:{}".format(
            "0.0.0.0" if self.fujinet_webui_host is None else self.fujinet_webui_host,
            8000 if self.fujinet_webui_port is None else self.fujinet_webui_port
        )


cfg = Config()
