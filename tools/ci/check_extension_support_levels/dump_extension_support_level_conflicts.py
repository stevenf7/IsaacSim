# Dump Extension Support Level Conflicts
#
# This script is executed within a Kit runtime environment to collect and validate extension
# support level data. It analyzes extension dependencies to ensure they follow support level
# rules and outputs any conflicts or errors to a JSON file.
#
# Support Level Rules Validated:
# 1. No extension should have "Internal" support level (legacy)
# 2. No extension should depend on another extension with "Internal" support level
# 3. Core support level extensions cannot depend on Sample support level extensions
#    (unless the dependency is marked as optional)
# 4. Extensions with "Enterprise" support level should be updated to "Core" (legacy)
#
# How to run:
#   This script is NOT run directly. It is executed by check_extension_support_levels.py
#   using Kit's --exec flag:
#
#   kit.exe <kit_file> --exec "dump_extension_support_level_conflicts.py <output_file> <extensions...>"
#
# The script is called as part of:
#   ./repo.sh ci check_extension_support_levels
#
# Which is configured in repo_internal.toml:
#   [repo_ci.jobs.check_extension_support_levels]
#   script = "${root}/tools/ci/check_extension_support_levels/check_extension_support_levels.py"
#
# Arguments:
#   output_file: Path where the JSON results will be written
#   extensions: One or more extension names or kit files to analyze
#
# Output:
#   JSON file containing extension support level conflicts and errors with structure:
#   {
#     "data": [
#       {
#         "id": "extension.name",
#         "support_level": "core",
#         "conflicts": {
#           "count": 2,
#           "enterprise": [...],
#           "internal": [...],
#           "core": [...]
#         },
#         "errors": [...]
#       }
#     ]
#   }
#

import json
import sys
from enum import Enum

import omni.kit.app


class ConflictType(str, Enum):
    """Enumeration of extension support level conflict types.

    Defines the types of conflicts that can occur when validating extension
    support level dependencies.
    """
    ENTERPRISE = "enterprise"
    INTERNAL = "internal"
    CORE = "core"


class SupportLevelExtension:
    """Represents an extension with support level validation information.

    Tracks an extension's support level, dependencies, and any conflicts or errors
    found during validation.

    Args:
        extension_info: Dictionary containing extension metadata including ID, support
            level, and dependencies.
    """
    def __init__(self, extension_info):
        # Base Extension Information
        self.ext_info = extension_info  # Extension Info Dictionary
        self.id = self.ext_info.get("package/id", None)  # Extension ID
        self.support_level: str = self.ext_info.get("package/support_level", "Sample").lower()

        # Support Level Validation
        self.dependencies = self.ext_info.get("dependencies", None)
        self.conflicts = {"enterprise": [], "internal": [], "core": []}
        self.errors = []

    @property
    def conflict_count(self) -> int:
        """Get the total number of conflicts for this extension.

        Returns:
            The sum of all conflicts across all conflict types.
        """
        return sum([len(self.conflicts[k]) for k in self.conflicts.keys()])

    @property
    def error_count(self) -> int:
        """Get the total number of errors for this extension.

        Returns:
            The number of errors encountered during validation.
        """
        return len(self.errors)

    @property
    def json(self) -> dict:
        """Get a JSON-serializable representation of the extension.

        Returns:
            Dictionary containing extension ID, support level, conflicts, and errors.
        """
        return {
            "id": self.id,
            "support_level": self.support_level,
            "conflicts": {
                "count": self.conflict_count,
                "enterprise": self.conflicts["enterprise"],
                "internal": self.conflicts["internal"],
                "core": self.conflicts["core"],
            },
            "errors": self.errors,
        }

    def add_conflict(self, name: str, support_level: str, optional: bool, conflict_type: ConflictType):
        """Add a support level conflict to this extension.

        Args:
            name: The ID of the conflicting extension or dependency.
            support_level: The support level of the conflicting extension.
            optional: Whether the conflicting dependency is optional.
            conflict_type: The type of conflict being recorded.
        """
        self.conflicts[conflict_type.value].append(
            {
                "id": name,
                "support_level": support_level.lower(),
                "optional": optional,
            }
        )

    def add_error(self, name: str, message: str):
        """Add an error encountered during validation.

        Args:
            name: The ID of the extension or dependency that caused the error.
            message: Description of the error.
        """
        error_dict = {"id": name, "error": message}
        self.errors.append(error_dict)


def _dump_extension_support_level_data(extension_list: list[str]) -> dict:
    """Collect and validate extension support level data.

    Resolves all extensions and their dependencies from the provided list, then validates
    that they follow support level rules. Identifies conflicts such as dependencies on
    Internal support level extensions, Core extensions depending on Sample extensions,
    and legacy Enterprise support level usage.

    Args:
        extension_list: List of extension names or kit files to analyze.

    Returns:
        Dictionary containing validation results with conflicts and errors for each
        extension that violates support level rules.
    """
    # Create the Manager object and sync registry so it is up to date
    manager = omni.kit.app.get_app_interface().get_extension_manager()
    print(f"> Syncing registry...")
    manager.sync_registry()
    print(f"> Registry synced.")
    
    print(f"> Solving extensions for: {extension_list}")
    # Collect the extensions from the extension list
    result, extensions, err = manager.solve_extensions(extension_list, add_enabled=True, return_only_disabled=False)
    
    if not result:
        print(f"> ERROR: Failed to solve extensions: {err}")
        print(f">   Extension list: {extension_list}")
    
    print(f"> Found {len(extensions)} extensions from extension list.")

    # Create the list of IDs
    dependency_ids = [ext["id"] for ext in extensions]

    # Container to hold all extensions that may have conflicts with support level
    parsed_extensions = []

    # Iterate through the extensions. Determine if an extension and its dependencies follow the following rules:
    # - Extension does not have an Internal Support Level
    # - Extension _dependency_ does not have Internal Support Level
    # - Extension, if Core support level, can not depend on an extension with Sample support level unless `optional`
    # - If Extension is a Kit Extension and Enterprise, it does not depend on any other support level
    for id_ in dependency_ids:

        # Skip if self identification of kit file or extension.
        # Skip if self identification of kit file or extension.
        # Since id_ is the full name, we have to inversely check if the listed extension against id_.
        should_skip = False
        for listed_ext in extension_list:
            if listed_ext in id_:
                should_skip = True
                break
        if should_skip:
            continue

        # This gets the full dict with support_level information
        ext_info = manager.get_extension_dict(id_)
        # Create the SupportLevelExtension object
        extension = SupportLevelExtension(ext_info)

        # Check to see if it is Enterprise, as its support level is legacy and should be made 'Core'.
        if extension.support_level == "enterprise":
            extension.add_conflict(extension.id, extension.support_level, False, ConflictType.ENTERPRISE)

        # Check to see if extension has dependencies
        if not extension.dependencies:
            continue

        for dep_name in extension.dependencies:
            # Find the ID in our solved extension list. If we can't find it we need to fetch the latest version
            dep_id = next((id_ for id_ in dependency_ids if id_.startswith(dep_name)), None)

            # If we can't identify the ID, Check if the dependency is optional. If not we add error.
            if dep_id is None:
                if not extension.dependencies[dep_name].get("optional", False):
                    extension.add_error(dep_name, f"{dep_name}: {extension.dependencies[dep_name]}")

                continue

            dep_info = manager.get_extension_dict(dep_id)  # Grab the dependency info.
            if dep_info == None:
                if not (dep_info := manager.get_registry_extension_dict(dep_id)):
                    msg = "Could not retrieve the extension dictionary from Extension Manager."
                else:
                    msg = "Could not retrieve the extension Support Level from registry extension dict as a fallback."
                extension.add_error(dep_id, msg)
                continue

            dep_support_level = dep_info.get(
                "package/support_level", "Sample"
            ).lower()  # Capture the extension support level
            dep_optional = ext_info.get(f"dependencies/{dep_name}/optional", False)

            # Compare the extension support level against the dependency support level
            # Fail case A: No extension should ever depend on another extension with Internal Support Level
            if dep_support_level == "internal":
                extension.add_conflict(dep_id, dep_support_level, dep_optional, ConflictType.INTERNAL)

            # Fail case B: Core extensions should not depend on another extension with Sample Support Level
            is_core_and_has_sample_dependency: bool = (
                extension.support_level == "core" and dep_support_level == "sample"
            )

            # If one of these two rules are encountered, we capture the conflict data
            # To return to the end user.
            if is_core_and_has_sample_dependency and not dep_optional:
                extension.add_conflict(dep_id, dep_support_level, dep_optional, ConflictType.CORE)

        parsed_extensions.append(extension)

    # Convert the parsed extension objects to a Dictionary
    ext_dict: dict = {"data": []}

    for ext in parsed_extensions:
        if ext.conflict_count > 0 or ext.error_count > 0:  # Only add Extensions with conflicts
            ext_dict["data"].append(ext.json)

    return ext_dict


def _main():
    """Main function that executes after Kit startup.

    Parses command line arguments to get the output file path and extension list,
    collects extension support level data, writes results to a JSON file, and
    initiates Kit shutdown.
    """
    print("> Starting extension support level check...")
    
    if len(sys.argv) < 2:
        print("Usage: To be run against Kit executable using the --exec flag. ")
        print(
            """
            import omni.repo.ci

            omni.repo.ci.launch(
                [
                    "${root}/_build/linux-x86_64/release/kit.sh",
                    "--exec",
                    f"tools/ci/dump_extension_support_level_conflicts.py <output_filepath> <extension/kit file>, <...>",
                ]
            )
            """
        )
        print(" ")
        print(
            "Reads the dependencies of the resolved extensions and writes them to a file if they fail the following rules:"
        )
        print("- Extension does not have an Internal Support Level")
        print("- Extension _dependency_ does not have Internal Support Level")
        print(
            "- Extension, if Core support level, can not depend on an extension with Sample support level unless `optional`"
        )
        print("- Extension is a Kit Extension and Enterprise, it does not depend on any other support level")
        omni.kit.app.get_app().post_quit(1)
        return

    print(f"> Raw sys.argv: {sys.argv}")
    print(f"> sys.argv length: {len(sys.argv)}")
    
    # When using --exec, Kit passes the script path as argv[0] and the kit file path as argv[1]
    # The actual script arguments come after that
    # We need to find where our actual arguments start (after the --exec flag)
    
    # Find the --exec argument and get everything after it
    exec_index = -1
    for i, arg in enumerate(sys.argv):
        if '--exec' in arg:
            exec_index = i
            break
    
    if exec_index >= 0 and exec_index + 1 < len(sys.argv):
        # The argument after --exec contains our script call
        exec_arg = sys.argv[exec_index + 1]
        # Parse the exec argument to extract our actual arguments
        parts = exec_arg.split()
        if len(parts) >= 3:  # script_path output_file extension_name
            output_file_name = parts[1]
            solve_extension_list = parts[2:]
        else:
            print(f"> ERROR: Invalid --exec argument format: {exec_arg}")
            omni.kit.app.get_app().post_quit(1)
            return
    else:
        # Fallback to old behavior if --exec not found
        output_file_name = sys.argv[1]
        solve_extension_list = sys.argv[2:]
    
    print(f"> Arguments received:")
    print(f">   Output file: {output_file_name}")
    print(f">   Extension list: {solve_extension_list}")

    try:
        # Capture the support level data
        ext_dict = _dump_extension_support_level_data(solve_extension_list)

        # Write the data out to file
        with open(output_file_name, "w") as fw:
            json.dump(ext_dict, fw, indent=2)
        print(f"> Wrote extension support level conflicts to {output_file_name}.")

        # Use Kit's proper shutdown mechanism with fast shutdown mode
        # This forces extensions to shut down quickly without waiting for cleanup
        print(f"> Initiating fast shutdown...")
        import carb
        carb.settings.get_settings().set("/app/fastShutdown", True)
        omni.kit.app.get_app().post_uncancellable_quit(0)
    except Exception as e:
        print(f"ERROR: Failed to dump extension support level conflicts: {e}")
        import traceback
        traceback.print_exc()
        import carb
        carb.settings.get_settings().set("/app/fastShutdown", True)
        omni.kit.app.get_app().post_uncancellable_quit(1)


if __name__ == "__main__":
    # Call main function directly (synchronous execution like dump_all_template_full_dependencies.py)
    _main()
