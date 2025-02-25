#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ExtensionValidator:
    # Dictionary of folders to ignore for specific extensions
    IGNORED_FOLDERS = {
        "isaacsim.ros2.bridge": ["isaac_ros2_messages"],  # Example: ignore isaac_ros2_messages folder that is
    }

    def __init__(self, extension_path):
        self.extension_path = Path(extension_path)
        self.extension_name = self.extension_path.name
        self.errors = []
        # Get the list of folders to ignore for this extension
        self.ignored_folders = self.IGNORED_FOLDERS.get(self.extension_name, [])

    def validate_extension_name(self):
        pattern = r"^isaacsim\.[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$"
        if not re.match(pattern, self.extension_name):
            self.errors.append(
                f"Invalid extension name format: {self.extension_name}\n"
                "Valid examples: \n"
                "- isaacsim.asset.gen.omap\n"
                "- isaacsim.simulation_manager\n"
                "- isaacsim.ros2.tf_viewer\n"
                "- isaacsim.tools.converter\n\n"
            )

    def validate_bindings(self):
        bindings_path = self.extension_path / "bindings"
        if bindings_path.exists():
            ext_bindings = bindings_path / self.extension_name
            if not ext_bindings.exists():
                self.errors.append(
                    f"Missing extension folder in bindings: {self.extension_name}\n" f"Expected: {ext_bindings}"
                )
            else:
                expected_binding_file = f"{self.get_ext_name()}Bindings.cpp"
                binding_file = ext_bindings / expected_binding_file
                if not binding_file.exists():
                    # Find any cpp files that exist in this directory
                    existing_cpp_files = list(ext_bindings.glob("*.cpp"))
                    error_msg = [
                        f"Missing bindings file: {binding_file}\n"
                        f"For extension '{self.extension_name}', the bindings file should be:\n"
                        f"bindings/{self.extension_name}/{expected_binding_file}\n"
                        "For example:\n"
                        "- isaacsim.my_ext -> bindings/isaacsim.my_ext/IsaacsimMyExtBindings.cpp\n"
                        "- isaacsim.ros2.tf -> bindings/isaacsim.ros2.tf/IsaacsimRos2TfBindings.cpp"
                    ]
                    if existing_cpp_files:
                        error_msg.append("\nFound non-compliant cpp files:")
                        for file in existing_cpp_files:
                            error_msg.append(f"- {file.name} (should be {expected_binding_file})")

                    self.errors.append("\n".join(error_msg))

    def validate_config(self):
        config_path = self.extension_path / "config"
        if not config_path.exists():
            self.errors.append("Missing required config folder\n" f"Expected: {config_path}")
        elif not (config_path / "extension.toml").exists():
            self.errors.append("Missing required extension.toml file\n" f"Expected: {config_path}/extension.toml")

    def validate_data(self):
        data_path = self.extension_path / "data"
        if not data_path.exists():
            self.errors.append("Missing required data folder\n" f"Expected: {data_path}")
        else:
            for required_file in ["icon.png", "preview.png"]:
                if not (data_path / required_file).exists():
                    self.errors.append(
                        f"Missing required file in data folder: {required_file}\n"
                        f"Expected: {data_path}/{required_file}"
                    )

    def validate_docs(self):
        docs_path = self.extension_path / "docs"
        if not docs_path.exists():
            self.errors.append("Missing required docs folder\n" f"Expected: {docs_path}")
        else:
            for required_file in ["CHANGELOG.md", "README.md", "index.rst"]:
                if not (docs_path / required_file).exists():
                    self.errors.append(
                        f"Missing required file in docs folder: {required_file}\n"
                        f"Expected: {docs_path}/{required_file}"
                    )

    def validate_include(self):
        include_path = self.extension_path / "include"
        if include_path.exists():
            ext_path = include_path / self.extension_name.replace(".", "/")
            if not ext_path.exists():
                self.errors.append(
                    f"Invalid include folder structure for: {self.extension_name}\n" f"Expected: {ext_path}"
                )

            # Check that only header files exist in include directory
            for file_path in include_path.rglob("*"):
                if file_path.is_file() and not file_path.name.endswith(".h"):
                    self.errors.append(
                        f"Non-header file found in include directory: {file_path}\n"
                        "Only .h files are allowed in the include directory"
                    )

    def validate_nodes(self):
        nodes_path = self.extension_path / "nodes"
        if nodes_path.exists():
            # Validate config folder and CategoryDefinition.json
            config_path = nodes_path / "config" / "CategoryDefinition.json"
            if not config_path.exists():
                self.errors.append("Missing CategoryDefinition.json in nodes/config\n" f"Expected: {config_path}")

            # Validate icons folder and svg file
            icons_path = nodes_path / "icons"
            if not icons_path.exists():
                self.errors.append("Missing icons folder in nodes\n" f"Expected: {icons_path}")
            elif not any(f.endswith(".svg") for f in os.listdir(icons_path)):
                self.errors.append(
                    "Missing .svg file in nodes/icons\n" f"Expected: At least one .svg file in {icons_path}"
                )

            # Validate Ogn files and corresponding cpp files
            ogn_files = {f.stem: f for f in nodes_path.glob("Ogn*.ogn")}
            cpp_files = {f.stem: f for f in nodes_path.glob("Ogn*.cpp")}

            # Check for .ogn files without matching .cpp files
            for ogn_stem in ogn_files:
                if ogn_stem not in cpp_files:
                    self.errors.append(
                        f"Missing corresponding .cpp file for {ogn_files[ogn_stem].name}\n" f"Expected: {ogn_stem}.cpp"
                    )

            # Check for .cpp files without matching .ogn files
            for cpp_stem in cpp_files:
                if cpp_stem not in ogn_files:
                    self.errors.append(
                        f"Found .cpp file without matching .ogn file: {cpp_files[cpp_stem].name}\n"
                        f"Expected: {cpp_stem}.ogn"
                    )

            # Check for non-Ogn cpp files (not allowed)
            non_ogn_cpp_files = list(nodes_path.glob("*.cpp"))
            non_ogn_cpp_files = [f for f in non_ogn_cpp_files if not f.name.startswith("Ogn")]
            if non_ogn_cpp_files:
                self.errors.append(
                    "Found .cpp files that do not correspond to .ogn files in nodes folder:\n"
                    f"{', '.join(f.name for f in non_ogn_cpp_files)}\n"
                    "All .cpp files in the nodes folder must have a matching .ogn file and start with 'Ogn'"
                )

            # Check for header files in nodes folder (not allowed)
            header_files = list(nodes_path.glob("*.h"))
            if header_files:
                self.errors.append(
                    "Header files are not allowed directly in the nodes folder\n"
                    f"Found header files: {', '.join(f.name for f in header_files)}"
                )

    def validate_plugins(self):
        plugins_path = self.extension_path / "plugins"
        if plugins_path.exists():
            ext_plugins = plugins_path / self.extension_name
            if not ext_plugins.exists():
                self.errors.append(
                    f"Missing extension folder in plugins: {self.extension_name}\n" f"Expected: {ext_plugins}"
                )

    def validate_python(self):
        python_path = self.extension_path / "python"
        if python_path.exists():
            # Validate impl folder
            impl_path = python_path / "impl"
            if not impl_path.exists():
                self.errors.append("Missing impl folder in python directory\n" f"Expected: {impl_path}")
            else:
                # Only __init__.py is required, extension.py is optional
                if not (impl_path / "__init__.py").exists():
                    self.errors.append(
                        "Missing required file in python/impl: __init__.py\n" f"Expected: {impl_path}/__init__.py"
                    )

            # Validate nodes folder if it exists
            nodes_path = python_path / "nodes"
            if nodes_path.exists():
                if not (nodes_path / "config" / "CategoryDefinition.json").exists():
                    self.errors.append(
                        "Missing CategoryDefinition.json in python/nodes/config\n"
                        f"Expected: {nodes_path}/config/CategoryDefinition.json"
                    )
                if not (nodes_path / "icons").exists():
                    self.errors.append("Missing icons folder in python/nodes\n" f"Expected: {nodes_path}/icons")
                elif not any(f.endswith(".svg") for f in os.listdir(nodes_path / "icons")):
                    self.errors.append(
                        "Missing .svg file in python/nodes/icons\n"
                        f"Expected: At least one .svg file in {nodes_path}/icons"
                    )

            # Validate tests folder if it exists
            tests_path = python_path / "tests"
            if tests_path.exists():
                if not (tests_path / "__init__.py").exists():
                    self.errors.append("Missing __init__.py in python/tests\n" f"Expected: {tests_path}/__init__.py")
                # Verify test file naming convention
                for file_path in tests_path.glob("*.py"):
                    if file_path.name not in ["__init__.py", "common.py"] and not file_path.name.startswith("test_"):
                        self.errors.append(
                            f"Invalid test file name: {file_path.name}\n"
                            "Test files must start with 'test_' (except for __init__.py and common.py)"
                        )

    def validate_file_naming(self):
        for file_path in self.extension_path.rglob("*"):
            # Skip files in ignored folders
            relative_path = file_path.relative_to(self.extension_path)
            folder_name = relative_path.parts[0] if relative_path.parts else ""
            if folder_name in self.ignored_folders:
                continue

            if file_path.is_file():
                if file_path.suffix == ".cpp" or file_path.suffix == ".h":
                    if not file_path.stem[0].isupper():
                        self.errors.append(
                            f"Invalid PascalCase naming: {file_path}\n"
                            "C++ source and header files must use PascalCase naming convention"
                        )

    def validate_premake(self):
        premake_path = self.extension_path / "premake5.lua"
        if not premake_path.exists():
            self.errors.append("Missing required premake5.lua file\n" f"Expected: {premake_path}")

    def get_ext_name(self):
        # First replace dots with underscores, then capitalize each word
        name_parts = self.extension_name.replace(".", "_").split("_")
        return "".join(part.capitalize() for part in name_parts)

    def validate(self):
        self.validate_extension_name()
        self.validate_bindings()
        self.validate_config()
        self.validate_data()
        self.validate_docs()
        self.validate_include()
        self.validate_nodes()
        self.validate_plugins()
        self.validate_python()
        self.validate_file_naming()
        self.validate_premake()

        return len(self.errors) == 0, self.errors


def validate_extension(path):
    validator = ExtensionValidator(path)
    is_valid, errors = validator.validate()

    if is_valid:
        print(f"Extension at {path} is valid!")
        return True
    else:
        print(f"Extension at {path} has the following errors:")
        for error in errors:
            # Split multi-line error messages and indent them properly
            for line in error.split("\n"):
                print(f"- {line}" if line == error.split("\n")[0] else f"  {line}")
        return False


def validate_extensions_in_directory(directory_path, recursive=False):
    """Validate all extensions in a directory."""
    directory = Path(directory_path)
    if not directory.exists():
        print(f"Directory {directory_path} does not exist.")
        return False

    all_valid = True

    if recursive:
        # Find all directories that might be extensions
        for path in directory.glob("**/isaacsim.*"):
            if path.is_dir():
                print(f"\nValidating extension: {path}")
                if not validate_extension(path):
                    all_valid = False
    else:
        # Only check immediate subdirectories that start with isaacsim.
        for path in directory.glob("isaacsim.*"):
            if path.is_dir():
                print(f"\nValidating extension: {path}")
                if not validate_extension(path):
                    all_valid = False

    return all_valid


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict[str, Any]) -> callable:
    """Setup the repo tool."""
    parser.add_argument(
        "extension_path",
        nargs="?",
        help="Path to the extension to validate. If not provided, will validate all extensions in the source/extensions directory.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively search for extensions in subdirectories.",
    )
    parser.add_argument(
        "-s",
        "--source-dir",
        default="${root}/source/extensions",
        help="Source directory containing extensions (default: ${root}/source/extensions).",
    )

    return run_tool


def run_tool(args: argparse.Namespace, config: Dict[str, Any]) -> int:
    """Run the extension structure validation tool."""
    # If a specific extension path is provided, validate just that extension
    if hasattr(args, "extension_path") and args.extension_path:
        extension_path = args.extension_path
        if not os.path.exists(extension_path):
            print(f"Error: Extension path {extension_path} does not exist.")
            return 1

        is_valid = validate_extension(extension_path)
        return 0 if is_valid else 1

    # Otherwise, validate all extensions in the source directory
    source_dir = args.source_dir if hasattr(args, "source_dir") else "${root}/source/extensions"
    # Replace ${root} with the actual root path
    source_dir = source_dir.replace("${root}", config.get("root", "."))

    print(f"Validating extensions in {source_dir}")
    is_valid = validate_extensions_in_directory(source_dir, args.recursive if hasattr(args, "recursive") else False)

    return 0 if is_valid else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_extension_structure.py <extension_path>")
        sys.exit(1)

    is_valid = validate_extension(sys.argv[1])
    sys.exit(0 if is_valid else 1)
