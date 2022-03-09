# FujiNet-PC Launcher

Brings [#FujiNet](https://fujinet.online/) experience into [Altirra](https://virtualdub.org/altirra.html) Atari emulator. It is simple launcher GUI to control [FujiNet-PC](https://github.com/FujiNetWIFI/fujinet-pc) and [NetSIO hub](https://github.com/FujiNetWIFI/fujinet-emulator-bridge). 

![Launcher](launcher.png)

Written in Python, using wxWidgets for GUI. It can run on Windows, macOS and Linux.



![Launcher on Windows](img/launcher-windows.png)
![Launcher on macOS](img/launcher-macos.png)

Note: Wine can be used to run Altirra on macOS and Linux.

## What does Fujinet-PC Launcher do?
- FujiNet-PC is launched in background
- NetSIO hub is launched in background to bridge FujiNet into Atari emulator
- Monitors both programs, user can stop them and/or restart them
- Click to open FujiNet-PC "SD Card" folder
- Allows to open FujiNet WebUI in default web browser
- FujiNet logs available via Log window
- Status LED's (FujiNet-PC running, NetSIO hub running, SIO active)
- "A" buton with Disk Swap function
- Command line options to control FujiNet-PC and NetSIO hub
  * parameters to control SD folder, config file, network ports
  * allows multiple Altirra-FujiNet instances to run simultaneously

## Installation

Check the instructions [here](Install.md) to get it running (currently only Windows, rest will follow).
