import os
import sys
import subprocess
import argparse

# This must be set in teamcity as a configuration parameter for this to work.
# teamcity.git.fetchAllHeads=true


def line_filter(line, ignore_filter):
    if ignore_filter:
        return True
    if line.startswith("Merge: "):
        return False
    if line.startswith("Author: "):
        return False
    return True


def generate_changes(compare_branch=None, ignore_filter=False):
    if not compare_branch:
        compare_branch = os.getenv("GENERATE_CHANGES")
        if not compare_branch:
            print("No branch to compare against specified...")
            sys.exit(1)

    self_branch = (
        subprocess.Popen(["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=subprocess.PIPE)
        .stdout.read()
        .decode("utf8")
    )

    print(f"Using revisions {compare_branch} > {self_branch}")
    if not os.path.exists("_build"):
        os.makedirs("_build")
    with open("_build/change_log.txt", "w", encoding="utf-8") as output:
        p = subprocess.Popen(
            f"git log {compare_branch} {self_branch.strip()}", stdout=subprocess.PIPE, encoding="utf-8"
        )
        git_output = p.communicate()[0]
        if p.returncode != 0:
            print("Error getting changes")
            sys.exit(p.returncode)
        for line in git_output.split("\n"):
            if line_filter(line, ignore_filter):
                output.write(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--compare-branch", dest="compare_branch", help="Branch to compare against", default=None, required=False
    )
    parser.add_argument(
        "-i",
        "--ignore-filter",
        dest="ignore_filter",
        help="Ignore the line filter, email and merge commits will be included",
        default=False,
        required=False,
    )
    options = parser.parse_args()

    generate_changes(compare_branch=options.compare_branch, ignore_filter=options.ignore_filter)


if __name__ == "__main__":
    main()
