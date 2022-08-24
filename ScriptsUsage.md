# FujiNet-PC scripts

The scripts package contains Launcher GUI and NetSIO hub Python modules and NetSIO custom device for Altirra. It does not contain any binaries. To run scripts Python 3 with necessary libraries must be installed on the system and FujiNet-PC binaries ([downloaded](https://github.com/FujiNetWIFI/fujinet-pc/releases) or [built](https://github.com/FujiNetWIFI/fujinet-pc#build-instructions)) have to be placed into `fujinet-pc` directory.

## Linux, macOS, Window

### Download and extract the files

[Download](https://github.com/a8jan/fujinet-pc-launcher/releases/latest) the **scripts** package and extract the files.

There are four subdirectories inside:

* `emulator` contains custom device for Altirra
* `fujinet-pc` is placeholder for FujiNet-PC binary
* `launcher` is Python module containing FujiNet-PC Launcher
* `netsiohub` is Python module containing NetSIO hub

### Python

Python 3 is required to run Launcher and NetSIO hub.

Check if Python version 3.x is installed:

```sh
$ python -V
Python 3.10.4
```

if command is not found or version 2.x.y is reported by `python` command try to use `python3` command instead:

```sh
$ python3 -V
Python 3.10.4
```

On Ubuntu it is possible to enable Python 3 via `python` command by installing `python-is-python3` package:
```sh
$ sudo apt install python-is-python3
```

Linux distros are likely shipped with some version of Python installed by default or at least available as ready to install package. For other systems if Python 3 is not installed yet it can be downloaded and installed from [https://www.python.org/](https://www.python.org/).

For recent Windows versions Python is available from Microsoft Store. Version 3.9 or 3.10 should work fine. It can be also installed using `winget`:

```sh
$ winget install -i Python.Python.3.9
```

Similar on macOS, if using package manager, e.g. homebrew, Python can be installed with it:

```sh
$ brew install python3
```

### NetSIO hub

Skip this step if you plan to use Launcher.

If not interested into Launcher GUI the NetSIO hub can be started manually. Enter the scripts directory - the one with `emulator`, `fujinet-pc`, `launcher` and `netsiohub` subdirectories (DO NOT enter `netsiohub` subdirectory).

Start NetSIO hub:

```sh
$ python -m netsiohub  # or python3 -m netsiohub
```

NetSIO hub command line options:

```
usage: netsiohub [-h] [--netsio-port NETSIO_PORT] [-d] [--port PORT] [-v]

Connects NetSIO protocol (SIO over UDP) talking peripherals with NetSIO Altirra custom device (localhost TCP).

options:
  -h, --help            show this help message and exit
  --netsio-port NETSIO_PORT
                        Change UDP port used by NetSIO peripherals (default 9997)
  -d, --debug           Print debug output
  --port PORT           Change TCP port used by Altirra NetSIO custom device (default 9996)
  -v, --verbose         Log emulation device commands
```

### FujiNet-PC

To allow the Launcher to control (start/stop and monitor) FujiNet-PC program the directory `fujinet-pc` must be populated with FujiNet-PC. Copy here the content of `build/dist` if it was built manually. Pre-build binaries for selected systems can be [downloaded](https://github.com/FujiNetWIFI/fujinet-pc/releases/latest) and files extracted here.

The content of `fujinet-pc` directory should look like this:

```sh
% ls -l fujinet-pc
drwx------   3 a8jan  staff       96 Aug 24 12:26 SD
drwx------  11 a8jan  staff      352 Aug 24 12:26 data
-rwx------   1 a8jan  staff      535 Aug 24 12:26 fnconfig.ini
-rwx------   1 a8jan  staff  6189712 Aug 24 12:26 fujinet
-rwx------   1 a8jan  staff      284 Aug 24 12:26 run-fujinet
```
On Windows there will be additional DLL files together with `fujinet.exe`

If you do not plan to use Launcher to start/stop FujiNet-PC the FujiNet-PC can be started manually. Enter `fujinet-pc` directory and start FujiNet-PC with `./run-fujinet` on Linux and Mac, use `run-fujinet.bat` on Windows.

FujiNet-PC command line options:

```
Usage: fujinet [-V] [-u URL] [-c config_file] [-s SD_directory]
```

### Launcher

FujiNet-PC Launcher uses [wxPython](https://wxpython.org/) library for its GUI. Check if it is installed:

```sh
$ python -c "import wx; print(wx.version())"
4.1.2a1.dev5310+af8cca51 msw (phoenix) wxWidgets 3.1.5
```

If instead of version information the `ModuleNotFoundError: No module named 'wx` is printed then wxPython must be installed. Easiest way is to install additional software for Python is to use **pip** - package installer for Python.

Note: Similar story to `python` vs `python3` is with `pip` vs `pip3` or even `python -m pip` vs `python3 -m pip`. Use the right pip command to manage Python 3 packages on your system (check Python version with `pip -V` or `pip3 -V`).

To install wxPython using `pip` (or `pip3`):

```sh
$ pip install -U wxPython  # or pip3 install -U wxPython
```

This should work fine on macOS and Windows. Unfortunately, not on Linux - details [here](https://wxpython.org/pages/downloads/).

There are two solutions to problem with wxPython installation on Linux:

a) Use package provided by Linux distribution

E.g on Ubuntu (quite old version):
```sh
$ sudo apt install python3-wxgtk4.0
```

b) Use Linux distribution [specific pip package](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/)

E.g on Ubuntu 22.04:
```sh
$ pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04/ wxPython
```

Now, with Python and wxPython installed, the Launcher program can be started. Enter the scripts directory - the one with `emulator`, `fujinet-pc`, `launcher` and `netsiohub` subdirectories (DO NOT enter `launcher` subdirectory).

Start FujiNet-PC Launcher:

```sh
$ python -m launcher  # or python3 -m launcher
```

If all is good the FujiNet shaped window will open and FujiNet-PC and NetSIO hub will be started in background.


FujiNet-PC Launcher command line options:

```
usage: launcher [-h] [-l LABEL] [-g GUI_SCALE] [-t] [-u URL] [-c FNCONFIG] [-s SD] [-p PORT] [-r NETSIO_PORT]
                [-i INSTANCE] [-v] [-d] [-V]

This launcher program controls FujiNet-PC and NetSIO hub

options:
  -h, --help            show this help message and exit
  -l LABEL, --label LABEL
                        Launcher label
  -g GUI_SCALE, --gui-scale GUI_SCALE
                        GUI scale
  -t, --top-window      Stay on top window
  -u URL, --url URL     FujiNet web interface ([0.0.0.0][:8000])
  -c FNCONFIG, --fnconfig FNCONFIG
                        Path to FujiNet configuration file (fnconfig.ini)
  -s SD, --sd SD        Path to SD directory (SD)
  -p PORT, --port PORT  TCP port used by Altirra NetSIO custom device (9996)
  -r NETSIO_PORT, --netsio-port NETSIO_PORT
                        UDP port used by NetSIO peripherals (9997)
  -i INSTANCE, --instance INSTANCE
                        FujiNet instance ID
  -v, --verbose         Log emulation device commands
  -d, --debug           Print debug output
  -V, --version         Print program version and exit
```


### Custom device for Altirra emulator

Device file for Altirra emulator `netsio.atdevice` is located in `emulator/Altirra` directory.

To connect Altirra with FujiNet follow the instructions [here](Install.md#4-connect-altirra-with-fujinet).
