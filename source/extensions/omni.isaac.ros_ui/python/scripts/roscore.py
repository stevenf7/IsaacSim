import subprocess
import sys
import signal
import psutil


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        print("killing child: ", process)
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
        self.roscore_process = None
        self.roscore_pid = None

    def check_running(self):
        import rosgraph

        try:
            rosgraph.Master("/rostopic").getPid()
        except:
            print("ROS master is not running")
            return False
        else:
            print("ROS master is already running")
            return True

    def startup(self, python_path, ros_path, prefix):
        ros_env = {}
        if self.check_running() == True:
            print("Not starting internal roscore")
            return
        # Get ros env parameters from bash setup script
        try:
            self.bash_process = subprocess.check_output(
                f"export {prefix}={ros_path}; source {ros_path}/setup.sh; env -0", shell=True, executable="/bin/bash"
            )
            for line in self.bash_process.decode("ascii").split("\0"):
                result = line.split("=")
                if len(result) == 2:
                    ros_env[result[0]] = result[1]

        except OSError as e:
            sys.stderr.write("roscore could not be run")
            raise e

        try:
            # append path to specified python bin folder
            ros_env["PATH"] = f"{python_path}:{ros_path}/bin:/bin"
            # + ros_env["PATH"]
            # print(ros_env)
            # running roscore will output logs, rosmaster --core disables rosout
            self.roscore_process = subprocess.Popen(["rosmaster --core"], shell=True, cwd=f"{ros_path}", env=ros_env)
            self.roscore_pid = self.roscore_process.pid  # pid of the roscore process (which has child processes)
        except OSError as e:
            sys.stderr.write("roscore could not be run")
            raise e

    def shutdown(self):
        if self.roscore_pid is not None and self.roscore_process is not None:
            print("try to kill child pids of roscore pid: " + str(self.roscore_pid))
            kill_child_processes(self.roscore_pid)
            self.roscore_process.terminate()
            self.roscore_process.wait()  # important to prevent from zombie process
        Roscore.__initialized = False
