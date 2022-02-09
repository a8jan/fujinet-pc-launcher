import sys

def main():
    # dispatcher
    # - if this code is started instead of python interpreter (pyinstaller) call netsiohub module
    # - otherwise continue to launcher module
    if len(sys.argv) >=2 and sys.argv[1] == '-u':
        del sys.argv[1]
    if len(sys.argv) >=3 and sys.argv[1] == '-m' and sys.argv[2] == 'netsiohub':
        import netsiohub.netsiohub as netsiohub
        del sys.argv[1]
        del sys.argv[1]
        return netsiohub.main() or 0
    else:
        try:
            import launcher.launcher as launcher
            return launcher.main() or 0
        except KeyboardInterrupt:
            return 1


if __name__ == "__main__":
    sys.exit(main())
