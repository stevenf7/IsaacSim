# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


# Add color code constants
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Function to check if color should be disabled
def should_disable_color():
    """Check if color output should be disabled based on environment variables or terminal type."""
    if "NO_COLOR" in os.environ or "TERM" in os.environ and os.environ["TERM"] == "dumb":
        return True
    return False


# Function to apply color to text
def colorize(text, color_code):
    """Apply color to text if color is enabled."""
    if should_disable_color():
        return text
    return f"{color_code}{text}{Colors.RESET}"


class ExtensionValidator:
    # Dictionary of folders to ignore for specific extensions
    IGNORED_FOLDERS = {
        "isaacsim.ros2.bridge": ["isaac_ros2_messages"],  # Example: ignore isaac_ros2_messages folder that is
    }

    def __init__(self, extension_path):
        self.extension_path = Path(extension_path)
        self.extension_name = self.extension_path.name
        self.errors = []
        self.warnings = []  # Add warnings list for less critical issues
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

            # Check if api.rst is required based on bindings or Python implementation
            needs_api_rst = False
            reason = ""

            # Check if bindings folder exists
            bindings_path = self.extension_path / "bindings"
            if bindings_path.exists():
                needs_api_rst = True
                reason = "contains a bindings folder"

            # Check if python/impl folder contains .py files other than extension.py
            python_impl_path = self.extension_path / "python" / "impl"
            if python_impl_path.exists():
                py_files = [
                    f for f in python_impl_path.glob("*.py") if f.name != "extension.py" and f.name != "__init__.py"
                ]
                if py_files:
                    needs_api_rst = True
                    reason = "contains Python implementation files"

            # If api.rst is needed but doesn't exist, add an error
            if needs_api_rst and not (docs_path / "api.rst").exists():
                self.errors.append(
                    f"Missing api.rst file in docs folder for extension that {reason}\n"
                    f"Expected: {docs_path}/api.rst"
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
            else:
                # Parse CategoryDefinition.json to get category names
                try:
                    with open(config_path, "r") as f:
                        category_def = json.load(f)

                    # Extract category names from CategoryDefinition.json
                    category_names = []
                    if "categoryDefinitions" in category_def:
                        # In this format, category names are the keys in the categoryDefinitions object
                        # (excluding special keys like $description)
                        for category_name, category_description in category_def["categoryDefinitions"].items():
                            if not category_name.startswith("$"):  # Skip special keys like $description
                                category_names.append(category_name)

                    # Check if CategoryDefinition.json has any categories defined
                    if not category_names:
                        self.errors.append(
                            f"No categories defined in CategoryDefinition.json\n"
                            f"CategoryDefinition.json must define at least one category"
                        )

                    # Validate .ogn files have matching categories
                    ogn_files = list(nodes_path.glob("Ogn*.ogn"))
                    for ogn_file in ogn_files:
                        with open(ogn_file, "r") as f:
                            ogn_content = f.read()

                        try:
                            # Parse the .ogn file as JSON to check for required fields
                            ogn_json = json.loads(ogn_content)

                            # Get the node definition (first object inside the root object)
                            if len(ogn_json) != 1:
                                self.errors.append(
                                    f"Invalid .ogn file structure in {ogn_file.name}\n"
                                    f"Expected exactly one root object"
                                )
                                continue

                            node_name = list(ogn_json.keys())[0]
                            node_def = ogn_json[node_name]

                            # Check for required fields
                            required_fields = ["version", "description", "categories"]
                            missing_fields = [field for field in required_fields if field not in node_def]

                            if missing_fields:
                                self.errors.append(
                                    f"Missing required fields in {ogn_file.name}: {missing_fields}\n"
                                    f"Every .ogn file must have the following fields: {required_fields}"
                                )

                            # Check that categoryDefinitions and icon are either both present or both absent
                            has_category_definitions = "categoryDefinitions" in node_def
                            has_icon = "icon" in node_def

                            if has_category_definitions != has_icon:
                                if has_category_definitions:
                                    self.errors.append(
                                        f"Missing 'icon' field in {ogn_file.name}\n"
                                        f"When 'categoryDefinitions' is present, 'icon' must also be present"
                                    )
                                else:
                                    self.errors.append(
                                        f"Missing 'categoryDefinitions' field in {ogn_file.name}\n"
                                        f"When 'icon' is present, 'categoryDefinitions' must also be present"
                                    )

                            # Check categories field
                            if "categories" in node_def:
                                categories_value = node_def["categories"]

                                # Handle different formats of the categories field
                                if isinstance(categories_value, str):
                                    # Single category as a string
                                    ogn_categories = [categories_value]
                                elif isinstance(categories_value, list):
                                    # Categories as an array
                                    ogn_categories = categories_value
                                elif isinstance(categories_value, dict):
                                    # Categories as a dictionary - skip validation against CategoryDefinition.json
                                    continue
                                else:
                                    self.errors.append(
                                        f"Invalid 'categories' format in {ogn_file.name}\n"
                                        f"Expected a string, array, or dictionary"
                                    )
                                    continue

                                # Check if the .ogn file has at least one category
                                if not ogn_categories:
                                    self.errors.append(
                                        f"Empty 'categories' in {ogn_file.name}\n"
                                        f"Every .ogn file must have at least one category"
                                    )
                                    continue

                                # Check if at least one category in the .ogn file matches a category in CategoryDefinition.json
                                matched_categories = [cat for cat in ogn_categories if cat in category_names]
                                if not matched_categories:
                                    self.errors.append(
                                        f"None of the categories {ogn_categories} in {ogn_file.name} match any category in CategoryDefinition.json\n"
                                        f"At least one category must match. Categories in CategoryDefinition.json: {', '.join(category_names)}"
                                    )

                        except json.JSONDecodeError:
                            self.errors.append(f"Invalid JSON in .ogn file: {ogn_file.name}")
                            continue

                except json.JSONDecodeError:
                    self.errors.append(f"Invalid JSON in CategoryDefinition.json: {config_path}")
                except Exception as e:
                    self.errors.append(f"Error processing CategoryDefinition.json or .ogn files: {str(e)}")

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

                    # Check if header files with CARB_PLUGIN_INTERFACE start with 'I'
                    if file_path.suffix == ".h":
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if "CARB_PLUGIN_INTERFACE" in content and not file_path.stem.startswith("I"):
                                    self.errors.append(
                                        f"Invalid interface naming: {file_path}\n"
                                        "Header files containing CARB_PLUGIN_INTERFACE must start with a capital 'I'"
                                    )
                        except Exception as e:
                            self.warnings.append(
                                f"Could not read file {file_path} to check for CARB_PLUGIN_INTERFACE: {str(e)}"
                            )

                    # Check if C++ files with CARB_PLUGIN_IMPL are named PluginInterface.cpp
                    if file_path.suffix == ".cpp":
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if "CARB_PLUGIN_IMPL" in content and file_path.name != "PluginInterface.cpp":
                                    self.errors.append(
                                        f"Invalid plugin implementation file name: {file_path}\n"
                                        "Files containing CARB_PLUGIN_IMPL must be named PluginInterface.cpp"
                                    )
                        except Exception as e:
                            self.warnings.append(
                                f"Could not read file {file_path} to check for CARB_PLUGIN_IMPL: {str(e)}"
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

        return len(self.errors) == 0, self.errors, self.warnings


def validate_extension(path):
    validator = ExtensionValidator(path)
    is_valid, errors, warnings = validator.validate()

    if is_valid:
        print(colorize(f"✓ Extension at {path} is valid!", Colors.GREEN + Colors.BOLD))

        # Print warnings if any
        if warnings:
            print(colorize("\nWarnings:", Colors.YELLOW + Colors.BOLD))
            for warning in warnings:
                for line in warning.split("\n"):
                    print(colorize(f"- {line}" if line == warning.split("\n")[0] else f"  {line}", Colors.YELLOW))

        return True
    else:
        print(colorize(f"✗ Extension at {path} has the following errors:", Colors.RED + Colors.BOLD))
        for error in errors:
            # Split multi-line error messages and indent them properly
            for line in error.split("\n"):
                print(colorize(f"- {line}" if line == error.split("\n")[0] else f"  {line}", Colors.RED))

        # Print warnings if any
        if warnings:
            print(colorize("\nWarnings:", Colors.YELLOW + Colors.BOLD))
            for warning in warnings:
                for line in warning.split("\n"):
                    print(colorize(f"- {line}" if line == warning.split("\n")[0] else f"  {line}", Colors.YELLOW))

        return False


def validate_extensions_in_directory(directory_path, recursive=False):
    """Validate all extensions in a directory."""
    directory = Path(directory_path)
    if not directory.exists():
        print(colorize(f"Directory {directory_path} does not exist.", Colors.RED))
        return False

    all_valid = True
    valid_count = 0
    invalid_count = 0
    total_count = 0

    if recursive:
        # Find all directories that might be extensions
        for path in directory.glob("**/isaacsim.*"):
            if path.is_dir():
                total_count += 1
                print(colorize(f"\nValidating extension: {path}", Colors.CYAN + Colors.BOLD))
                if validate_extension(path):
                    valid_count += 1
                else:
                    invalid_count += 1
                    all_valid = False
    else:
        # Only check immediate subdirectories that start with isaacsim.
        for path in directory.glob("isaacsim.*"):
            if path.is_dir():
                total_count += 1
                print(colorize(f"\nValidating extension: {path}", Colors.CYAN + Colors.BOLD))
                if validate_extension(path):
                    valid_count += 1
                else:
                    invalid_count += 1
                    all_valid = False

    # Print summary
    print(colorize("\n=== Validation Summary ===", Colors.BOLD))
    print(f"Total extensions checked: {colorize(str(total_count), Colors.BOLD)}")
    print(f"Valid extensions: {colorize(str(valid_count), Colors.GREEN)}")
    print(f"Invalid extensions: {colorize(str(invalid_count), Colors.RED)}")

    if all_valid:
        print(colorize("\n✓ All extensions are valid!", Colors.GREEN + Colors.BOLD))
    else:
        print(colorize(f"\n✗ {invalid_count} extension(s) have validation errors.", Colors.RED + Colors.BOLD))

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
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )

    # Get the list of extensions to ignore from config
    ignored_extensions = config.get("repo_check_extension_structure", {}).get("ignored_extensions", [])
    parser.add_argument(
        "--ignored-extensions",
        nargs="+",
        default=ignored_extensions,
        help="List of extension names to ignore during validation.",
    )

    return run_tool


def run_tool(args: argparse.Namespace, config: Dict[str, Any]) -> int:
    """Run the extension structure validation tool."""
    # Set color mode based on arguments
    if hasattr(args, "no_color") and args.no_color:
        os.environ["NO_COLOR"] = "1"

    # Get the list of extensions to ignore
    ignored_extensions = args.ignored_extensions if hasattr(args, "ignored_extensions") else []

    # If a specific extension path is provided, validate just that extension
    if hasattr(args, "extension_path") and args.extension_path:
        extension_path = args.extension_path
        if not os.path.exists(extension_path):
            print(colorize(f"Error: Extension path {extension_path} does not exist.", Colors.RED + Colors.BOLD))
            return 1

        # Check if this extension should be ignored
        extension_name = Path(extension_path).name
        if extension_name in ignored_extensions:
            print(colorize(f"Skipping validation for ignored extension: {extension_name}", Colors.YELLOW))
            return 0

        is_valid = validate_extension(extension_path)
        return 0 if is_valid else 1

    # Otherwise, validate all extensions in the source directory
    source_dir = args.source_dir if hasattr(args, "source_dir") else "${root}/source/extensions"
    # Replace ${root} with the actual root path
    source_dir = source_dir.replace("${root}", config.get("root", "."))

    print(colorize(f"Validating extensions in {source_dir}", Colors.CYAN + Colors.BOLD))

    # Modify validate_extensions_in_directory to skip ignored extensions
    directory = Path(source_dir)
    if not directory.exists():
        print(colorize(f"Directory {source_dir} does not exist.", Colors.RED))
        return 1

    all_valid = True
    valid_count = 0
    invalid_count = 0
    ignored_count = 0
    total_count = 0

    recursive = args.recursive if hasattr(args, "recursive") else False

    if recursive:
        # Find all directories that might be extensions
        for path in directory.glob("**/isaacsim.*"):
            if path.is_dir():
                total_count += 1
                # Check if this extension should be ignored
                if path.name in ignored_extensions:
                    print(colorize(f"\nSkipping ignored extension: {path.name}", Colors.YELLOW))
                    ignored_count += 1
                    continue

                print(colorize(f"\nValidating extension: {path}", Colors.CYAN + Colors.BOLD))
                if validate_extension(path):
                    valid_count += 1
                else:
                    invalid_count += 1
                    all_valid = False
    else:
        # Only check immediate subdirectories that start with isaacsim.
        for path in directory.glob("isaacsim.*"):
            if path.is_dir():
                total_count += 1
                # Check if this extension should be ignored
                if path.name in ignored_extensions:
                    print(colorize(f"\nSkipping ignored extension: {path.name}", Colors.YELLOW))
                    ignored_count += 1
                    continue

                print(colorize(f"\nValidating extension: {path}", Colors.CYAN + Colors.BOLD))
                if validate_extension(path):
                    valid_count += 1
                else:
                    invalid_count += 1
                    all_valid = False

    # Print summary
    print(colorize("\n=== Validation Summary ===", Colors.BOLD))
    print(f"Total extensions found: {colorize(str(total_count), Colors.BOLD)}")
    print(f"Ignored extensions: {colorize(str(ignored_count), Colors.YELLOW)}")
    print(f"Valid extensions: {colorize(str(valid_count), Colors.GREEN)}")
    print(f"Invalid extensions: {colorize(str(invalid_count), Colors.RED)}")

    if all_valid:
        print(colorize("\n✓ All non-ignored extensions are valid!", Colors.GREEN + Colors.BOLD))
    else:
        print(colorize(f"\n✗ {invalid_count} extension(s) have validation errors.", Colors.RED + Colors.BOLD))

    return 0 if all_valid else 1


if __name__ == "__main__":
    # Add command line argument for color
    parser = argparse.ArgumentParser(description="Validate Isaac Sim extension structure")
    parser.add_argument("extension_path", nargs="?", help="Path to the extension to validate")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    # Set color mode based on arguments
    if args.no_color:
        os.environ["NO_COLOR"] = "1"

    if not args.extension_path:
        print(colorize("Usage: python check_extension_structure.py <extension_path>", Colors.YELLOW))
        sys.exit(1)

    is_valid = validate_extension(args.extension_path)
    sys.exit(0 if is_valid else 1)
