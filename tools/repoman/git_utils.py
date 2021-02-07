import re
import sys
import os
import logging
from typing import List

import omni.repo.man.nvenv as nvenv
import omni.repo.man

logger = logging.getLogger(os.path.basename(__file__))


class Commit:
    def __init__(self):
        self.hash = ""
        self.is_merge = False
        self.author = ""
        self.email = ""
        self.date = ""
        self.message = []

    def is_empty(self):
        return not self.hash and not self.author and not self.email and not self.message

    def __str__(self):
        return (
            str(self.is_merge)
            + " "
            + self.author.ljust(15)
            + "  "
            + self.email[:20].ljust(20)
            + "  "
            + self.hash[:7].ljust(8)
            + "  "
            + str(self.message)
        )


commits = []


def parseCommit(commitLines):
    commit = Commit()
    # iterate lines and save
    for nextLine in commitLines:
        if nextLine == "" or nextLine == "\n":
            # ignore empty lines
            pass
        elif bool(re.match("commit", nextLine, re.IGNORECASE)):
            # commit xxxx
            if not commit.is_empty():  ## new commit, so re-initialize
                commits.append(commit)
                commit = Commit()
            commit.hash = re.match("commit (.*)", nextLine, re.IGNORECASE).group(1)
        elif bool(re.match("merge:", nextLine, re.IGNORECASE)):
            commit.is_merge = True
        elif bool(re.match("author:", nextLine, re.IGNORECASE)):
            # Author: xxxx <xxxx@xxxx.com>
            m = re.compile("Author: (.*) <(.*)>").match(nextLine)
            commit.author = m.group(1)
            commit.email = m.group(2)
        elif bool(re.match("date:", nextLine, re.IGNORECASE)):
            pass
        elif bool(re.match("    ", nextLine, re.IGNORECASE)):
            # (4 empty spaces)
            text = nextLine.strip()
            if text:
                commit.message.append(nextLine.strip())
        else:
            print("ERROR: Unexpected Line: " + nextLine)


def generate_log(repo_location_path, additional_log_args=None):

    git_args = ["log", "--first-parent"]
    if additional_log_args:
        git_args.extend(additional_log_args)
    ret_dict = nvenv.execute_git(git_args, repo_location_path)

    stdout = ret_dict["stdout"].splitlines()

    parseCommit(stdout)

    # We skip merge commits and assume the next commit is a squash commit which contains the summary
    # (possibly a bit optimistic?)
    log = []
    for c in commits:
        if c.is_merge:
            if len(c.message) > 1:
                log.append(c.message[1] + " (" + c.author + ")\n")
            else:
                log.append(c.message[0] + " (" + c.author + ")\n")
        else:
            log.append(c.message[0] + " (" + c.author + ")\n")
    return log


def call_git_safe(root, args, timeout=60):
    print("> git {}".format(" ".join(args)))
    git_output = omni.repo.man.execute_git(args, cwd=root, timeout=timeout)

    if git_output["returncode"] != 0:
        logger.error("Git command '{}' failed with: '{}'".format(args, git_output))
        sys.exit(-1)
    print(git_output["stdout"])
    return git_output["stdout"]


def generate_kit_commit_log(
    start_commit: str, end_commit: str, branch: str = "master", clone_depth: int = 100
) -> List[str]:
    log = []
    with omni.repo.man.nvenv.TemporaryDirectory() as tmp_dir_path:
        # Switch off lfs filtering which is the slowest part
        call_git_safe(tmp_dir_path, ["config", "--global", "filter.lfs.smudge", '"git-lfs smudge --skip"'])
        # Check the value has been set correctly
        call_git_safe(tmp_dir_path, ["config", "--global", "filter.lfs.smudge"])
        # Do the clone
        # Could also use https://gitlab-master.nvidia.com/omniverse/repo/repo_source/-/blob/master/omni/repo/source/main.py#L21
        # but I'm not planning on having this code around for long
        stdout = call_git_safe(
            tmp_dir_path,
            [
                "clone",
                "https://gitlab-master.nvidia.com/omniverse/kit/",
                "--single-branch",
                "--branch",
                branch,
                "--depth",
                str(clone_depth),
                tmp_dir_path,
            ],
            timeout=600,
        )
        print(stdout)
        # Restore state of filtering
        call_git_safe(tmp_dir_path, ["config", "--global", "filter.lfs.smudge", '"git-lfs smudge -- %f"'])
        print("cloned to", tmp_dir_path)
        log = generate_log(tmp_dir_path, ["%s..%s" % (start_commit, end_commit)])
    return log
