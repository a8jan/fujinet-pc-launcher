# FujiNet-PC Launcher

Simple launcher GUI to control FujiNet-PC and NetSIO hub.

## Build

### Windows

```cmd
pyinstaller --clean --onedir --noconfirm --noconsole --python-option u --name launcher --icon launcher\images\launcher-bg.ico --add-data launcher\images;images  launcher\__main__.py
```
