# Build instructions

The idea is to automate the build process to create the bundle zip file with all needed components: [FujiNet-PC](https://github.com/FujiNetWIFI/fujinet-pc), [SD Card](https://github.com/FujiNetWIFI/fujinet-sd-card) files and [Bridge to the emulator](https://github.com/FujiNetWIFI/fujinet-emulator-bridge). This is work in progress.

The instructions below may be incomplete. I need to keep my notes somewhere ;-)

## Prerequisites

```sh
git clone https://github.com/FujiNetWIFI/fujinet-emulator-bridge.git
git clone https://github.com/a8jan/fujinet-pc-launcher.git
```

NetSIO hub from emulator bridge repository is written in Python as well FujiNet-PC Launcher is written in Python. To reduce the overhead of PyInstaller result both modules (netsiohub and launcher) are bundled together - this way only one Python interpreter with libraries is added for both programs.

Before build, both python modules should be inside `fujinet-pc-launcher`. Copy `netsiohub` module directory from `fujinet-emulator-bridge/fujinet-bridge` into `fujinet-pc-launcher` (or create symlink instead of copy).

When done, inside `fujinet-pc-launcher` there should be two module directories:
- launcher
- netsiohub


## Windows

To build Windows executable using PyInstaller:

```cmd
cd fujinet-pc-launcher
pyinstaller --clean --onedir --noconfirm --noconsole --python-option u  --name launcher --icon launcher\images\launcher-bg.ico --add-data launcher\images;images  launcher\__main__.py
```

The result is in `dist` directory.

## macOS

To build macOS launcher.app using PyInstaller:

```sh
pyinstaller --clean --onedir --noconfirm --noconsole --python-option u --name launcher --icon launcher/images/launcher-bg.ico --add-data launcher/images:images  launcher/__main__.py
```

## Linux

To build Linux AppImage:

```sh
TBD
```

## Pack them all

Build FujiNet-PC `dist` target. Copy the result from `fujinet-pc/build/dist` as `fujinet-pc` (rename `dist` to `fujinet-pc`) into `fujinet-pc-launcher/dist` directory.

Create `emulator` directory inside `fujinet-pc-launcher/dist` and copy `netsio.atdev` from `fujinet-emulator-bridge/altirra-custom-device` into newly created `emulator` directory.

The content of `fujinet-pc-launcher/dist` should be
- launcher
- fujinet-pc
- emulator

Zip `fujinet-pc-launcher/dist/*` into `fujinet-pc-bundle.zip`
