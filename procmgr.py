import signal
import sys
import platform
import subprocess
import threading
import queue
from pathlib import Path


class FujiNetMgr(threading.Thread):
    SHUTDOWN = -1
    PROC_START = 1
    PROC_STOP = 2
    PROC_RESTART = 3

    def __init__(self, log):
        self.log = log
        self.control_q = queue.Queue()
        self.proc = None
        self.redirect = None
        super().__init__()

    def start_process(self):
        self.control_q.put(self.PROC_START)

    def stop_process(self):
        self.control_q.put(self.PROC_STOP)

    def restart_process(self):
        self.control_q.put(self.PROC_RESTART)

    def shutdown(self):
        self.control_q.put(self.SHUTDOWN)
        self.join()  # TODO make non-blocking

    def run(self):
        # print("FujiNetMgr started.")
        while True:
            try:
                # check for control message
                msg = self.control_q.get(timeout=1.)
            except queue.Empty:
                # self.log.write('.')
                # check if redirect still runs
                if self.redirect is not None and not self.redirect.is_alive():
                    self.log.write("output closed\n")
                    self.redirect.join()
                    self.redirect = None
                # check if process still runs
                if self.proc is not None and self.proc.poll() is not None:
                    rc = self.proc.poll()
                    self.proc = None
                    self.log.write("fujinet ended ({})\n".format(rc))
                    if rc == 75:
                        self.start_process()
            else:
                if self._handle_control_msg(msg):
                    break
        # print("FujiNetMgr stopped.")

    def _handle_control_msg(self, msg):
        self.log.write("control message: {}\n".format(msg))
        # handle control message
        if msg == self.SHUTDOWN:
            self._proc_stop()
            return True
        if msg == self.PROC_START:
            self._proc_start()
        elif msg == self.PROC_STOP:
            self._proc_stop()
        elif msg == self.PROC_RESTART:
            self._proc_stop()
            self._proc_start()
        return False

    def is_running(self):
        if self.proc is not None:
            rc = self.proc.poll()
            if rc is None:
                return True
        return False

    def _proc_start(self):
        """start process and do I/O redirect"""
        if self.proc is not None:
            rc = self.proc.poll()
            if rc is None:
                self.log.write("fujinet is already running\n")
                return
            if self.redirect is not None:
                self.redirect.join()
                self.redirect = None

        # TODO use "fujinet-pc" this is just to make test&dev easier
        cwd = Path(sys.argv[0]).parent.resolve() / "fujinet-pc-{}".format(
            {
                "linux": "ubuntu",
                "darwin": "macos",
                "windows": "windows"
            }.get(platform.system().lower(), "unknown")
        )
        cmd = cwd / "fujinet.exe" if platform.system() == "Windows" else "./fujinet"
        self.log.write("Starting command {} in {}\n".format(cmd, cwd))
        try:
            self.proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                         creationflags=0 if sys.platform != 'win32' else
                                         subprocess.CREATE_NEW_PROCESS_GROUP)
        except:
            self.log.write("ERROR {} starting {}\n".format(sys.exc_info()[1], "ping"))
            self.proc = None
            self.redirect = None
        else:
            self.log.write("Running fujinet\n")
            self.redirect = Redirect(self.proc.stdout, self.log)
            self.redirect.start()

    def _proc_stop(self):
        if self.proc is None:
            self.log.write("fujinet is not running\n")
            return
        self.log.write("Stopping fujinet\n")
        # send SIGTERM and wait
        if sys.platform != 'win32':
            self.proc.send_signal(signal.SIGTERM)
        else:
            self.proc.send_signal(signal.CTRL_BREAK_EVENT)
        rc = self.proc.poll()
        for i in range(6):
            if rc is not None:
                break
            try:
                rc = self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.log.write("fujinet is still running\n")
                rc = None
        if rc is None:
            # send SIGKILL
            self.log.write("Killing fujinet\n")
            self.proc.kill()
            rc = self.proc.wait()
        if self.redirect is not None:
            self.redirect.join()
            self.redirect = None
        self.proc = None
        self.log.write("fujinet stopped\n")


class Redirect(threading.Thread):
    def __init__(self, input, output):
        self.input = input
        self.output = output
        super().__init__()

    def run(self):
        while True:
            line = self.input.readline()
            if line:
                pass
                # # sys.stdout.write(line.decode())
                # # sys.stdout.flush()
                try:
                    self.output.write(line.decode())
                except UnicodeDecodeError:
                    # self.output.write(line.decode(errors='ignore').encode('ascii', 'backslashreplace'))
                    self.output.write(line.decode(errors='ignore'))
            else:
                break
