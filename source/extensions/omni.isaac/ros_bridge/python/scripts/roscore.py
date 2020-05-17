import subprocess
import shlex
import sys
import signal
import psutil


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
        print(parent)
    except psutil.NoSuchProcess:
        print("parent process not existing")
        return
    children = parent.children(recursive=True)
    print(children)
    for process in children:
        print("try to kill child: " + str(process))
        process.send_signal(sig)


class Roscore(object):
    """
    roscore wrapped into a subprocess.
    Singleton implementation prevents from creating more than one instance.
    """

    __initialized = False

    def __init__(self):
        if Roscore.__initialized:
            raise Exception("You can't create more than 1 instance of Roscore.")
        Roscore.__initialized = True

    def startup(self):
        ros_env = {}
        # Get ros env parameters from bash setup script
        try:
            self.bash_process = subprocess.check_output(
                "source /opt/ros/melodic/setup.sh; env -0", shell=True, executable="/bin/bash"
            )
            for line in self.bash_process.decode("ascii").split("\0"):
                result = line.split("=")
                if len(result) == 2:
                    ros_env[result[0]] = result[1]

        except OSError as e:
            sys.stderr.write("roscore could not be run")
            raise e

        try:
            self.roscore_process = subprocess.Popen(["roscore"], env=ros_env)
            self.roscore_pid = self.roscore_process.pid  # pid of the roscore process (which has child processes)
        except OSError as e:
            sys.stderr.write("roscore could not be run")
            raise e

    def shutdown(self):
        print("try to kill child pids of roscore pid: " + str(self.roscore_pid))
        kill_child_processes(self.roscore_pid)
        self.roscore_process.terminate()
        self.roscore_process.wait()  # important to prevent from zombie process
        Roscore.__initialized = False
