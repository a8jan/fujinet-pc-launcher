# FujiNet-PC Launcher

TODO

Some random thoughts here for now ...

## Build

### Windows

```cmd
pyinstaller --clean --onedir --noconfirm --noconsole --python-option u --name launcher --icon launcher\images\launcher.ico --add-data launcher\images;images  launcher\__main__.py
```
