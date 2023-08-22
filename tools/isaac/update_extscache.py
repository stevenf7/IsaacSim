import argparse
from typing import Callable, Dict
from urllib.request import urlopen


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Update extensions cache (omni.isaac.sim.extscache.kit)."
    parser.add_argument(
        "-o",
        "--offline",
        dest="offline",
        required=False,
        default=False,
        help="Do not update the cache from Create. (default: will update the cache from Create)",
        action="store_true",
    )

    def run_repo_tool(options: Dict, config: Dict):
        print(
            'Please review the output of this script at ./source/apps/omni.isaac.sim.extscache.kit before committing changes to the repo. Run "./build.sh -u -r" to update the cache. See the results of the cache update at the bottom of the omni.isaac.sim.extscache.kit file. To make changes to the configuration of this script, edit ./repo.toml.'
        )

        if options.offline:
            print("Running in offline mode")

        # Read config info from ./repo.toml
        tool_config = config["repo_update_extscache"]

        # Read custom dependencies from ./repo.toml and convert to dict of {dep: ver} or {dep: (ver, tag)}
        deps_for_isaac = dict()
        deps_for_testing = dict()
        deps_for_ml = dict()
        override = dict()  # override version of a dependency to set specific versions regardless of version in Create

        # if dependency has a tag, it should have format {dep: "ext.name-ver", tag: "tag"} in repo.toml
        # if dependency does not have a tag, it should just be a string with format "ext.name-ver" in repo.toml
        for item in tool_config["deps_for_isaac"]:
            if type(item) is dict:
                (dep, _, ver) = item["dep"].partition("-")
                deps_for_isaac[dep] = (ver, item["tag"])
            else:
                (dep, _, ver) = item.partition("-")
                deps_for_isaac[dep] = ver

        for item in tool_config["deps_for_testing"]:
            if type(item) is dict:
                (dep, _, ver) = item["dep"].partition("-")
                deps_for_testing[dep] = (ver, item["tag"])
            else:
                (dep, _, ver) = item.partition("-")
                deps_for_testing[dep] = ver

        for item in tool_config["deps_for_ml"]:
            if type(item) is dict:
                (dep, _, ver) = item["dep"].partition("-")
                deps_for_ml[dep] = (ver, item["tag"])
            else:
                (dep, _, ver) = item.partition("-")
                deps_for_ml[dep] = ver
        for item in tool_config["override"]:
            if type(item) is dict:
                (dep, _, ver) = item["dep"].partition("-")
                override[dep] = (ver, item["tag"])
            else:
                (dep, _, ver) = item.partition("-")
                override[dep] = ver

        # These tuples contain the comment that will be printed above the dependencies for each set of custom dependencies
        deps = [
            ("Only for Isaac Sim", deps_for_isaac),
            ("Testing dependencies\n# internal only, used for benchmarking, removed from package", deps_for_testing),
            ("ML dependencies", deps_for_ml),
            (None, None),  # This is a marker that indicates that the next set of dependencies are the Create extensions
        ]

        # Get the names of extensions that are platform-specific (if a dependency is on this list but is not in Create or the custom dependencies, it will be ignored)
        windows_only = tool_config["windows_only"]
        linux_only = tool_config["linux_only"]

        # Get the names of extensions that should be excluded from the cache, even if they are in Create
        exclude = tool_config["exclude"]

        # Read the current dependencies from the cache
        dest_file = open(tool_config["output_file"], "r")
        dest_file_lines = dest_file.readlines()
        dest_file.close()
        commentline = 120 * "#" + "\n"

        enableds = dict()
        exacts = dict()

        if not options.offline:
            # Read the extensions from Create
            # exacts contains the "Exact Version dependencies" list from Create, enableds contains the "enabled" list from Create
            exacts, enableds = read_source(tool_config["url"])
        else:
            reached_enableds = False
            reached_exacts = False
            prev_line_os = False
            for line in dest_file_lines:
                if (reached_enableds or reached_exacts) and line.startswith(commentline):
                    break
                elif not reached_enableds and not reached_exacts and line.startswith("# Extensions from Create"):
                    reached_enableds = True
                    continue
                elif reached_enableds and not reached_exacts:
                    if line == "\n":
                        continue
                    elif line.startswith("# Additional Create Extensions"):
                        reached_exacts = True
                        continue
                    else:
                        line = line[0:-1].strip()  # remove the comment and trailing whitespaces
                        (dep, _, ver) = line.partition(" = ")  # separate the extension name from the version
                        dep = dep[1:-1]  # remove the quotes
                        (ver, _, _) = ver[1:-1].partition(", ")  # remove the curly braces, comma, and "exact = true"
                        (_, _, ver) = ver.partition(' = "')  # remove the "version = " text
                        ver = ver[:-1]  # remove the trailing quote
                        if dep in enableds:  # if the dependency is already in the dict, print an error
                            print("ERROR: duplicate exact dependency: " + dep)
                        else:  # otherwise, add it to the dict
                            enableds[dep] = ver
                        continue
                elif reached_exacts:
                    if line == "\n" or prev_line_os:
                        prev_line_os = False
                        continue
                    elif line.startswith("# Windows only") or line.startswith("# Linux only"):
                        prev_line_os = True
                        continue
                    else:
                        line = line[0:-1].strip()  # remove the comment and trailing whitespaces
                        (dep, _, ver) = line.partition(" = ")  # separate the extension name from the version
                        dep = dep[1:-1]  # remove the quotes
                        (ver, _, _) = ver[1:-1].partition(", ")  # remove the curly braces, comma, and "exact = true"
                        (_, _, ver) = ver.partition(' = "')  # remove the "version = " text
                        ver = ver[:-1]  # remove the trailing quote
                        if dep in exacts:  # if the dependency is already in the dict, print an error
                            print("ERROR: duplicate exact dependency: " + dep)
                        else:  # otherwise, add it to the dict
                            exacts[dep] = ver
                        continue

        # Add the Create extensions to the list of dependencies
        deps.append(("Extensions from Create", enableds))
        deps.append(("Additional Create Extensions", exacts))

        # Used to keep track of which dependencies are platform-specific
        windows = dict()
        linux = dict()

        # Used to store the new text that will be written to omni.isaac.sim.extscache.kit
        output = []

        # If there are dependencies currently in omni.isaac.sim.extscache.kit that were manually added to the top of the file, keep them
        for line in dest_file_lines:
            output.append(line)
            line = line.strip()

            # finding this line indicates that all future lines should be replaced
            if line.startswith("# BEGIN AUTOUPDATED PART"):
                output = output[:-1]

                # remove the extra commentline that was before "# BEGIN AUTOUPDATED PART"
                if output[-1].startswith(commentline):
                    output = output[:-1]
                break

            # ignore lines that are not dependencies
            elif line.startswith("#") or line.startswith("[dependencies]") or line == "" or line == "\n":
                continue

            # read the dependency, version, and tag (if present) from the line
            dep, _, info = line.partition(" = ")
            dep = dep[1:-1]
            info = info[1:-2].split(", ")
            if len(info) not in [2, 3]:
                print("ERROR: invalid dependency: " + line + " (ignore if this line is intentionally added)")
                continue

            # if the dependency is in the manually added list, it should not be in the custom lists or the lists from Create
            exclude.append(dep)

        create_exts = False
        output.append(commentline)
        output.append(
            "# BEGIN AUTOUPDATED PART (generated by ./repo.sh update_extscache, please use ./repo.toml to configure)\n"
        )
        output.append(commentline)
        output.append("\n")

        # For each set of dependencies, print the title and then print each dependency
        for title, dep_list in deps:
            # check for the None marker that indicates that the next set of dependencies are the Create extensions
            if title is None:
                create_exts = True
                continue

            # Print the section title
            output.append(f"# {title}\n")
            for dep, ver in dep_list.items():
                # If the dependency is in the list of dependencies to exclude, skip it
                if dep in exclude:
                    continue
                # If the dependency is in the list of dependencies to override, use the version from the override list
                if dep in override:
                    ver = override[dep]

                # If the dependency is in one of the platform-specific lists, add it to the list of platform-specific dependencies to be addressed later
                if dep in windows_only:
                    windows[dep] = ver
                    continue
                if dep in linux_only:
                    linux[dep] = ver
                    continue

                # If the dependency is in the list of custom dependencies, or if it is in the list of dependencies from Create and not in the list of custom dependencies (i.e. has already been printed), print it
                if not create_exts or (
                    create_exts and dep not in deps_for_isaac and dep not in deps_for_testing and dep not in deps_for_ml
                ):
                    output.append(print_dep(dep, ver))
            output.append("\n")

        # Print the platform-specific dependencies (if there are any)
        if len(windows) > 0:
            output.append('# Windows only\n[dependencies."filter:platform"."windows-x86_64"]\n')
            for dep, ver in windows.items():
                output.append(print_dep(dep, ver))
        if len(linux) > 0:
            output.append('# Linux only\n[dependencies."filter:platform"."linux-x86_64"]\n')
            for dep, ver in linux.items():
                output.append(print_dep(dep, ver))

        output.append("\n")
        output.append(commentline)
        output.append("# END AUTOUPDATED PART\n")
        output.append(commentline)

        # Write the output text to omni.isaac.sim.extscache.kit
        dest_file = open(tool_config["output_file"], "w")
        dest_file.writelines(output)
        dest_file.close()

    return run_repo_tool


# Read the dependencies from Create
def read_source(file):
    # Read the file from the given URL
    source_file = urlopen(file)
    source_file_lines = source_file.readlines()
    source_file.close()

    # exacts contains the "Exact Version dependencies" list from Create, enableds contains the "enabled" list from Create
    exacts = dict()
    enableds = dict()

    # These variables are used to keep track of which section of the file is currently being read
    generated = False
    exact = False
    enabled = False

    for line in source_file_lines:
        line = line.decode("utf-8")
        # Use the comments (and other text) in the file to determine which section is currently being read
        if not generated and line.startswith("# BEGIN GENERATED PART"):
            generated = True
            continue
        if generated and not exact and not enabled and line.startswith("# Exact Version dependencies"):
            exact = True
            continue
        if generated and exact and line == "\n":
            exact = False
            continue
        if generated and not exact and not enabled and line.startswith("enabled = ["):
            enabled = True
            continue
        if generated and enabled and line == "]\n":
            enabled = False
            continue
        if generated and line.startswith("# END GENERATED PART"):
            generated = False
            continue

        # If the line is not a comment or other text, it is a dependency (and it should be added to the correct dict depending on which section is being read)
        # This code does not handle the case where a dependency has a tag, since Create does not currently have any dependencies that have tags (and therefore the format is unknown)
        if exact:
            line = line[1:-1].strip()  # remove the comment and trailing whitespaces
            (dep, _, ver) = line.partition("-")  # separate the extension name from the version
            if dep in exacts:  # if the dependency is already in the dict, print an error
                print("ERROR: duplicate exact dependency: " + dep)
            else:  # otherwise, add it to the dict
                exacts[dep] = ver
            continue
        if enabled:
            line = line.strip()[
                1:-2
            ]  # remove the trailing whitespaces, quotes, and commas - this may cause an issue if the last dependency in Create's list ever has no comma
            (dep, _, ver) = line.partition("-")
            if dep in enableds:
                print("ERROR: duplicate enabled dependency: " + dep)
            else:
                enableds[dep] = ver
            continue

    return (exacts, enableds)


# Print a dependency in the format used by omni.isaac.sim.extscache.kit --> "extension.name" = {version = "version.number", exact = true}, or "extension.name" = {tag = "tag_name", version = "version.number", exact = true}
def print_dep(dep, ver):
    # If the version is a tuple, it contains the version and the tag
    if type(ver) is tuple:
        tag_text = f'tag = "{ver[1]}", '
        ver = ver[0]
    else:  # otherwise, there is no tag
        tag_text = ""

    # return the dependency in the correct format
    return f'"{dep}" = {{{tag_text}version = "{ver}", exact = true}}\n'
