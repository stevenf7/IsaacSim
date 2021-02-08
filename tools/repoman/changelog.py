import omni.repo.man
from datetime import datetime
import git_utils
from typing import List


def extract_commit_from_version_string(version_str):

    version_parts = omni.repo.man.update.version_to_parts(version_str)

    # TODO: package name formatting, it looks likes it's changed recently, from e.g:
    # 101.0+master.ff9d7df3.teamcity.23688.${platform}.release -> 101.0+master.24127.cf6bedeb.teamcity.${platform}.release
    # The only pattern I can see is the commit is the one BEFORE teamcity
    commit_index = 0
    if version_str.find("teamcity") != -1:
        for cnt, item in enumerate(version_parts):
            if item == "teamcity":
                commit_index = cnt - 1
    else:
        #  alternative convention is 100.3.41-6a03571f-release-${platform}-release
        commit_index = 3

    return version_parts[commit_index]


def write_log(version: str, start_commit: str, end_commit: str, commit_log: List[str], changelog_path):

    date = datetime.today().strftime("%Y-%m-%d")
    changeLog = f"## [{version}] - {date}\n\n"

    for entry in commit_log:
        changeLog = changeLog + "- " + entry

    with open(changelog_path, "r+") as f:
        content = f.read()
        f.seek(0, 0)
        # TODO: some magic number stuff to get rid of here...
        f.write(content[:140] + "\n" + changeLog + "\n" + content[141:])

    return commit_log
