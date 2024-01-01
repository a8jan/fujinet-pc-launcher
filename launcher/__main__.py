import sys

# FujiNet-PC Launcher
import launcher.launcher as launcher
# NetSIO Hub
import netsiohub.hub as netsiohub

def main():
    # dispatcher
    # - if this code is started instead of python interpreter (python -u -m netsiohub [args])
    #   continue as netsiohub (this happen with pyinstaller)
    # - otherwise continue to launcher module
    if len(sys.argv) >=4 and sys.argv[1] == '-u' and sys.argv[2] == '-m' and sys.argv[3] == 'netsiohub':
        del sys.argv[1]
        del sys.argv[1]
        del sys.argv[1]
        return netsiohub.main() or 0
    else:
        try:
            return launcher.main() or 0
        except KeyboardInterrupt:
            return 1


if __name__ == "__main__":
    sys.exit(main())
