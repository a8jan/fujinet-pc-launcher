import re
import signal
import sys
import subprocess
import threading
import queue
import requests

from launcher.config import cfg


class ProcessMgr(threading.Thread):
    # control messages
    SHUTDOWN = -1
    PROC_START = 1
    PROC_STOP = 2
    PROC_RESTART = 3

    # managed process status
    STATUS_STOPPED = 0
    STATUS_RUNNING = 1
    STATUS_STOPPING = 2

    def __init__(self, cmd, cwd, log, name=None):
        super().__init__()
        # control queue
        self.control_q = queue.Queue()
        # command with arguments to run
        self.proc_cmd = cmd
        # command working directory
        self.proc_cwd = cwd
        # write output/log messages to
        self.log = log
        # child process returned by subprocess.Popen
        self.proc = None
        # redirect thread
        self.redirect = None
        # process is being stopped
        self.stopping = False
        self.name = name or "Process" # -> "Process Manager"

    def start_process(self):
        self.control_q.put(self.PROC_START)

    def stop_process(self):
        self.control_q.put(self.PROC_STOP)

    def restart_process(self):
        self.control_q.put(self.PROC_RESTART)

    def shutdown(self):
        self.control_q.put(self.SHUTDOWN)
        # self.log.write("join {} Manager\n".format(self.name))
        # self.join()  # TODO make non-blocking
        # self.log.write("{} Manager joined\n".format(self.name))

    def run(self):
        self.log.write("{} Manager started.\n".format(self.name))
        while True:
            try:
                # check for control message
                msg = self.control_q.get(timeout=1.)
            except queue.Empty:
                msg = None
            # check if redirect still runs
            if self.redirect is not None and not self.redirect.is_alive():
                self.log.write("output closed\n")
                self.log.write("join redirect\n")
                self.redirect.join()
                self.log.write("redirect joined\n")
                self.redirect = None
            # check if process still runs
            if self.proc is not None:
                rc = self.proc.poll()
                if rc is not None:
                    self.proc = None
                    self.log.write("{} ended with exit code {}\n".format(self.name, rc))
                    if rc == 75:
                        self.start_process()
            # handle control message
            if msg is not None:
                if self._handle_control_msg(msg):
                    break
        self.log.write("{} Manager stopped.\n".format(self.name))

    def _handle_control_msg(self, msg):
        self.log.write("{} Manager control message: {}\n".format(self.name, msg))
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

    def status(self):
        if self.proc is not None:
            rc = self.proc.poll()
            if rc is None:
                return self.STATUS_RUNNING if not self.stopping else self.STATUS_STOPPING
        return self.STATUS_STOPPED

    def _proc_start(self):
        """start process and do I/O redirect"""
        if self.is_running():
            self.log.write("{} is already running\n".format(self.name))
            return

        # start fujinet process
        self.stopping = False
        self.log.write("Starting {}:\n  Command: {}\n  Directory: {}\n".format(self.name, self.proc_cmd, self.proc_cwd))
        creationflags = 0
        if sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        # start process
        try:
            self.proc = subprocess.Popen(
                self.proc_cmd, cwd=self.proc_cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=creationflags)
        except:
            self.log.write("Error starting {}: {}\n".format(self.name, sys.exc_info()[1]))
            self.proc = None
            self.redirect = None
        else:
            self.log.write("Running {}\n".format(self.name))
            # start child process output redirect thread
            self.redirect = Redirect(self.proc.stdout, self.log)
            self.redirect.start()

    def _proc_stop(self):
        if self.proc is None:
            self.log.write("{} is not running\n".format(self.name))
            return
        self.stopping = True
        # graceful stop
        rc = self._proc_graceful_stop()
        # if still running -> kill it
        if rc is None:
            self._proc_kill()
        # cleanup redirect
        if self.redirect is not None:
            self.log.write("join redirect\n")
            self.redirect.join()
            self.log.write("redirect joined\n")
            self.redirect = None
        # done
        self.proc = None
        self.stopping = False
        self.log.write("{} stopped\n".format(self.name))

    def _proc_graceful_stop(self):
        self.log.write("Stopping {}\n".format(self.name))
        # send SIGTERM or CTRL_BREAK
        if sys.platform == 'win32':
            self.log.write("ctrl+break to {}\n".format(self.proc.pid))
            self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            # os.kill(self.proc.pid, signal.CTRL_BREAK_EVENT)
            self.log.write("sent\n")
        else:
            self.proc.send_signal(signal.SIGTERM)
        # wait proc to finish
        self.log.write("polling proc\n")
        rc = self.proc.poll()
        self.log.write("poll result: {}\n".format(rc))
        for i in range(6):
            if rc is not None:
                break
            self.log.write("wait proc\n")
            try:
                rc = self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.log.write("{} is still running\n".format(self.name))
                rc = None
            self.log.write("wait result: {}\n".format(rc))
        return rc

    def _proc_kill(self):
        # send SIGKILL
        self.log.write("Killing {}\n".format(self.name))
        self.proc.kill()
        self.log.write("wait proc\n")
        rc = self.proc.wait()
        self.log.write("wait result: {}\n".format(rc))
        return rc


class FujiNetMgr(ProcessMgr):
    def __init__(self, log):
        cwd = cfg.fujinet_rundir
        cmd = [cfg.fujinet_path]
        # additional arguments
        if cfg.fujinet_listen_url is not None:
            cmd.extend(["-u", cfg.fujinet_listen_url])
        if cfg.fnconfig:
            # use specified fnconfig, if any
            cmd.extend(["-c", cfg.fnconfig])
        if cfg.sd_path:
            # use specified SD path, if any
            cmd.extend(["-s", cfg.sd_path])
        super().__init__(cmd, cwd, log, "FujiNet")

    def _proc_graceful_stop(self):
        self.log.write("Stopping {}\n".format(self.name))
        # on windows signals works only when proc is attached to console
        # exit fujinet via API call
        try:
            r = requests.get(cfg.fujinet_api_exit)
        except requests.RequestException as e:
            self.log.write("API call failed: {}\n".format(e))
        # wait proc to finish
        self.log.write("polling proc\n")
        rc = self.proc.poll()
        self.log.write("poll result: {}\n".format(rc))
        for i in range(6):
            if rc is not None:
                break
            self.log.write("wait proc\n")
            try:
                rc = self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.log.write("{} is still running\n".format(self.name))
                rc = None
            self.log.write("wait result: {}\n".format(rc))
        return rc


class NetSioMgr(ProcessMgr):
    def __init__(self, log):
        cwd = cfg.netsio_rundir
        cmd = [sys.executable, "-u", "-m", cfg.netsio_module]
        if cfg.atdev_port:
            cmd.extend(['--port', str(cfg.atdev_port)])
        if cfg.netsio_port:
            cmd.extend(['--netsio-port', str(cfg.netsio_port)])
        super().__init__(cmd, cwd, log, "NetSIO hub")

    def _proc_graceful_stop(self):
        # on windows signals works only when proc is attached to console
        if sys.platform == 'win32':
            # don't use signals on windows
            return self.proc.poll()
        else:
            return super()._proc_graceful_stop()


class Redirect(threading.Thread):
    def __init__(self, input, output):
        self.input = input
        self.output = output
        super().__init__()

    def run(self):
        while True:
            line = self.input.readline()
            if line:
                # # sys.stdout.write(line.decode())
                # # sys.stdout.flush()
                self.output.write(line.decode(errors='backslashreplace'))
                # try:
                #     self.output.write(line.decode())
                # except UnicodeDecodeError:
                #     # self.output.write(line.decode(errors='ignore').encode('ascii', 'backslashreplace'))
                #     self.output.write(line.decode(errors='ignore'))
            else:
                break
        self.output.write("EOF\n")
