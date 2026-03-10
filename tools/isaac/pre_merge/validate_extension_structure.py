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

"""Validate extension directory structure for Isaac Sim extensions."""

import argparse
import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import toml  # type: ignore[import-untyped]

# Ensure this script's directory is on sys.path so term_helpers (same dir) can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from term_helpers import Colors, colorize


def print_messages(messages: list[str], color: str) -> None:
    """Print a list of messages with proper indentation.

    Args:
        messages: List of messages to print.
        color: Color code to apply to the messages.
    """
    for message in messages:
        lines = message.split("\n")
        for i, line in enumerate(lines):
            prefix = "- " if i == 0 else "  "
            print(colorize(f"{prefix}{line}", color))


class ExtensionValidator:
    """Validate the structure and naming conventions of Isaac Sim extensions.

    Args:
        extension_path: Path to the extension directory to validate.
    """

    # Dictionary of folders to ignore for specific extensions
    IGNORED_FOLDERS = {
        "isaacsim.ros2.bridge": ["isaac_ros2_messages"],
    }

    def __init__(self, extension_path: str) -> None:
        self.extension_path = Path(extension_path)
        self.extension_name = self.extension_path.name
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.ignored_folders = self.IGNORED_FOLDERS.get(self.extension_name, [])

    def validate_extension_name(self) -> None:
        """Validate that the extension name follows the required pattern."""
        pattern = r"^isaacsim\.[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$"
        if not re.match(pattern, self.extension_name):
            self.errors.append(
                f"Invalid extension name format: {self.extension_name}\n"
                "Valid examples:\n"
                "- isaacsim.asset.gen.omap\n"
                "- isaacsim.simulation_manager\n"
                "- isaacsim.ros2.tf_viewer\n"
                "- isaacsim.tools.converter"
            )

    def validate_bindings(self) -> None:
        """Validate the bindings folder structure and required files."""
        bindings_path = self.extension_path / "bindings"
        if not bindings_path.exists():
            return

        ext_bindings = bindings_path / self.extension_name
        if not ext_bindings.exists():
            self.errors.append(
                f"Missing extension folder in bindings: {self.extension_name}\n" f"Expected: {ext_bindings}"
            )
            return

        expected_binding_file = f"{self._get_pascal_case_name()}Bindings.cpp"
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

    def validate_config(self) -> None:
        """Validate the config folder and extension.toml file."""
        config_path = self.extension_path / "config"
        if not config_path.exists():
            self.errors.append(f"Missing required config folder\nExpected: {config_path}")
            return

        toml_path = config_path / "extension.toml"
        if not toml_path.exists():
            self.errors.append(f"Missing required extension.toml file\nExpected: {toml_path}")
        else:
            self._validate_extension_toml(toml_path)

    def _validate_extension_toml(self, toml_path: Path) -> None:
        """Validate the extension.toml file content.

        Checks if the extension.toml file has the required configuration when the extension
        contains C++ files but no [[native.plugin]] entry.

        Args:
            toml_path: Path to the extension.toml file to validate.
        """
        try:
            with open(toml_path) as f:
                toml_content = toml.load(f)
        except Exception as e:
            self.errors.append(f"Error reading extension.toml: {e}")
            return

        # Check if extension has C++ files
        has_cpp_files = self._has_cpp_files()

        # Check if extension.toml has [[native.plugin]] entry
        has_native_plugin = "native" in toml_content and "plugin" in toml_content["native"]

        # Check if writeTarget.platform is set to true (it's under package section)
        write_target_platform = toml_content.get("package", {}).get("writeTarget", {}).get("platform", False)

        # If extension has C++ files but no [[native.plugin]] entry,
        # writeTarget.platform must be set to true
        if has_cpp_files and not has_native_plugin and not write_target_platform:
            self.errors.append(
                "Extension has C++ files but no [[native.plugin]] entry in extension.toml\n"
                "When an extension contains C++ files and does not have a [[native.plugin]] entry, "
                "writeTarget.platform must be set to true in extension.toml\n"
                "Add the following to your extension.toml:\n"
                "writeTarget.platform = true"
            )

    def _has_cpp_files(self) -> bool:
        """Check if the extension contains any C++ source files.

        Searches for .cpp files in common C++ directories and .h files in the include
        directory to determine if the extension contains C++ code.

        Returns:
            True if the extension contains C++ files, False otherwise.
        """
        # Check for .cpp files in various directories
        cpp_directories = [
            self.extension_path / "bindings",
            self.extension_path / "nodes",
            self.extension_path / "plugins",
            self.extension_path / "src",
        ]

        for directory in cpp_directories:
            if directory.exists() and list(directory.rglob("*.cpp")):
                return True

        # Also check for .h files in include directory as they indicate C++ code
        include_path = self.extension_path / "include"
        if include_path.exists() and list(include_path.rglob("*.h")):
            return True

        return False

    def validate_data(self) -> None:
        """Validate the data folder and required files."""
        data_path = self.extension_path / "data"
        if not data_path.exists():
            self.errors.append(f"Missing required data folder\nExpected: {data_path}")
            return

        for required_file in ["icon.png", "preview.png"]:
            if not (data_path / required_file).exists():
                self.errors.append(
                    f"Missing required file in data folder: {required_file}\n" f"Expected: {data_path}/{required_file}"
                )

    def validate_docs(self) -> None:
        """Validate the docs folder and required files."""
        docs_path = self.extension_path / "docs"
        if not docs_path.exists():
            self.errors.append(f"Missing required docs folder\nExpected: {docs_path}")
            return

        for required_file in ["CHANGELOG.md", "README.md"]:
            if not (docs_path / required_file).exists():
                self.errors.append(
                    f"Missing required file in docs folder: {required_file}\n" f"Expected: {docs_path}/{required_file}"
                )

        # Check if api.rst is required based on bindings or Python implementation
        if self._needs_api_rst():
            reason = self._get_api_rst_reason()
            if not (docs_path / "api.rst").exists():
                self.errors.append(
                    f"Missing api.rst file in docs folder for extension that {reason}\n"
                    f"Expected: {docs_path}/api.rst"
                )

        if (docs_path / "api.rst").exists() and not (docs_path / "index.rst").exists():
            self.errors.append(
                f"Missing index.rst file in docs folder (required when api.rst is present)\n"
                f"Expected: {docs_path}/index.rst"
            )

    def _needs_api_rst(self) -> bool:
        """Check if the extension needs an api.rst file.

        Returns:
            True if api.rst is required, False otherwise.
        """
        # Check if bindings folder exists
        if (self.extension_path / "bindings").exists():
            return True

        # Check if python/impl folder contains .py files other than extension.py and __init__.py
        python_impl_path = self.extension_path / "python" / "impl"
        if python_impl_path.exists():
            py_files = [f for f in python_impl_path.glob("*.py") if f.name not in ("extension.py", "__init__.py")]
            if py_files:
                return True

        return False

    def _get_api_rst_reason(self) -> str:
        """Get the reason why api.rst is required.

        Returns:
            A string describing why api.rst is required.
        """
        if (self.extension_path / "bindings").exists():
            return "contains a bindings folder"
        return "contains Python implementation files"

    def validate_include(self) -> None:
        """Validate the include folder structure and files."""
        include_path = self.extension_path / "include"
        if not include_path.exists():
            return

        ext_path = include_path / self.extension_name.replace(".", "/")
        if not ext_path.exists():
            self.errors.append(f"Invalid include folder structure for: {self.extension_name}\n" f"Expected: {ext_path}")

        # Check that only header files exist in include directory
        for file_path in include_path.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith(".h"):
                self.errors.append(
                    f"Non-header file found in include directory: {file_path}\n"
                    "Only .h files are allowed in the include directory"
                )

    def validate_nodes(self) -> None:
        """Validate the nodes folder structure and files."""
        nodes_path = self.extension_path / "nodes"
        if not nodes_path.exists():
            return

        self._validate_nodes_config(nodes_path)
        self._validate_nodes_icons(nodes_path)
        self._validate_nodes_files(nodes_path)

    def _validate_nodes_config(self, nodes_path: Path) -> None:
        """Validate CategoryDefinition.json and .ogn files in the nodes folder.

        Args:
            nodes_path: Path to the nodes directory.
        """
        config_path = nodes_path / "config" / "CategoryDefinition.json"
        if not config_path.exists():
            self.errors.append(f"Missing CategoryDefinition.json in nodes/config\nExpected: {config_path}")
            return

        try:
            with open(config_path) as f:
                category_def = json.load(f)

            # Extract category names from CategoryDefinition.json
            category_names = [name for name in category_def.get("categoryDefinitions", {}) if not name.startswith("$")]

            if not category_names:
                self.errors.append(
                    "No categories defined in CategoryDefinition.json\n"
                    "CategoryDefinition.json must define at least one category"
                )
                return

            # Validate .ogn files have matching categories
            self._validate_ogn_files(nodes_path, category_names)

        except json.JSONDecodeError:
            self.errors.append(f"Invalid JSON in CategoryDefinition.json: {config_path}")
        except Exception as e:
            self.errors.append(f"Error processing CategoryDefinition.json or .ogn files: {e}")

    def _validate_ogn_files(self, nodes_path: Path, category_names: list[str]) -> None:
        """Validate .ogn files in the nodes folder.

        Args:
            nodes_path: Path to the nodes directory.
            category_names: List of valid category names from CategoryDefinition.json.
        """
        ogn_files = list(nodes_path.glob("Ogn*.ogn"))
        for ogn_file in ogn_files:
            try:
                with open(ogn_file) as f:
                    ogn_json = json.load(f)

                if len(ogn_json) != 1:
                    self.errors.append(
                        f"Invalid .ogn file structure in {ogn_file.name}\n" "Expected exactly one root object"
                    )
                    continue

                node_name = next(iter(ogn_json))
                node_def = ogn_json[node_name]

                self._validate_ogn_required_fields(ogn_file.name, node_def)
                self._validate_ogn_category_icon_pairing(ogn_file.name, node_def)
                self._validate_ogn_categories(ogn_file.name, node_def, category_names)

            except json.JSONDecodeError:
                self.errors.append(f"Invalid JSON in .ogn file: {ogn_file.name}")

    def _validate_ogn_required_fields(self, filename: str, node_def: dict[str, Any]) -> None:
        """Validate that an .ogn file has all required fields.

        Args:
            filename: Name of the .ogn file being validated.
            node_def: The node definition from the .ogn file.
        """
        required_fields = ["version", "description", "categories"]
        missing_fields = [field for field in required_fields if field not in node_def]

        if missing_fields:
            self.errors.append(
                f"Missing required fields in {filename}: {missing_fields}\n"
                f"Every .ogn file must have the following fields: {required_fields}"
            )

    def _validate_ogn_category_icon_pairing(self, filename: str, node_def: dict[str, Any]) -> None:
        """Validate that categoryDefinitions and icon are either both present or both absent.

        Args:
            filename: Name of the .ogn file being validated.
            node_def: The node definition from the .ogn file.
        """
        has_category_definitions = "categoryDefinitions" in node_def
        has_icon = "icon" in node_def

        if has_category_definitions != has_icon:
            if has_category_definitions:
                self.errors.append(
                    f"Missing 'icon' field in {filename}\n"
                    "When 'categoryDefinitions' is present, 'icon' must also be present"
                )
            else:
                self.errors.append(
                    f"Missing 'categoryDefinitions' field in {filename}\n"
                    "When 'icon' is present, 'categoryDefinitions' must also be present"
                )

    def _validate_ogn_categories(self, filename: str, node_def: dict[str, Any], category_names: list[str]) -> None:
        """Validate the categories field in an .ogn file.

        Args:
            filename: Name of the .ogn file being validated.
            node_def: The node definition from the .ogn file.
            category_names: List of valid category names from CategoryDefinition.json.
        """
        if "categories" not in node_def:
            return

        categories_value = node_def["categories"]

        # Handle different formats of the categories field
        if isinstance(categories_value, str):
            ogn_categories = [categories_value]
        elif isinstance(categories_value, list):
            ogn_categories = categories_value
        elif isinstance(categories_value, dict):
            # Categories as a dictionary - skip validation against CategoryDefinition.json
            return
        else:
            self.errors.append(f"Invalid 'categories' format in {filename}\n" "Expected a string, array, or dictionary")
            return

        # Check if the .ogn file has at least one category
        if not ogn_categories:
            self.errors.append(f"Empty 'categories' in {filename}\n" "Every .ogn file must have at least one category")
            return

        # Check if at least one category matches CategoryDefinition.json
        matched_categories = [cat for cat in ogn_categories if cat in category_names]
        if not matched_categories:
            self.errors.append(
                f"None of the categories {ogn_categories} in {filename} match any category in CategoryDefinition.json\n"
                f"At least one category must match. Categories in CategoryDefinition.json: {', '.join(category_names)}"
            )

    def _validate_nodes_icons(self, nodes_path: Path) -> None:
        """Validate the icons folder in the nodes directory.

        Args:
            nodes_path: Path to the nodes directory.
        """
        icons_path = nodes_path / "icons"
        if not icons_path.exists():
            self.errors.append(f"Missing icons folder in nodes\nExpected: {icons_path}")
        elif not list(icons_path.glob("*.svg")):
            self.errors.append(f"Missing .svg file in nodes/icons\nExpected: At least one .svg file in {icons_path}")

    def _validate_nodes_files(self, nodes_path: Path) -> None:
        """Validate .ogn and .cpp file pairing in the nodes directory.

        Args:
            nodes_path: Path to the nodes directory.
        """
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
        non_ogn_cpp_files = [f for f in nodes_path.glob("*.cpp") if not f.name.startswith("Ogn")]
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

    def validate_plugins(self) -> None:
        """Validate the plugins folder structure."""
        plugins_path = self.extension_path / "plugins"
        if not plugins_path.exists():
            return

        ext_plugins = plugins_path / self.extension_name
        if not ext_plugins.exists():
            self.errors.append(
                f"Missing extension folder in plugins: {self.extension_name}\n" f"Expected: {ext_plugins}"
            )

    def validate_python(self) -> None:
        """Validate the python folder structure and files."""
        python_path = self.extension_path / "python"
        if not python_path.exists():
            return

        self._validate_python_impl(python_path)
        self._validate_python_nodes(python_path)
        self._validate_python_tests(python_path)

    def _validate_python_impl(self, python_path: Path) -> None:
        """Validate the python/impl folder.

        Args:
            python_path: Path to the python directory.
        """
        impl_path = python_path / "impl"
        if not impl_path.exists():
            self.errors.append(f"Missing impl folder in python directory\nExpected: {impl_path}")
        elif not (impl_path / "__init__.py").exists():
            self.errors.append(f"Missing required file in python/impl: __init__.py\nExpected: {impl_path}/__init__.py")

    def _validate_python_nodes(self, python_path: Path) -> None:
        """Validate the python/nodes folder if it exists.

        Args:
            python_path: Path to the python directory.
        """
        nodes_path = python_path / "nodes"
        if not nodes_path.exists():
            return

        config_file = nodes_path / "config" / "CategoryDefinition.json"
        if not config_file.exists():
            self.errors.append(f"Missing CategoryDefinition.json in python/nodes/config\nExpected: {config_file}")

        icons_path = nodes_path / "icons"
        if not icons_path.exists():
            self.errors.append(f"Missing icons folder in python/nodes\nExpected: {icons_path}")
        elif not list(icons_path.glob("*.svg")):
            self.errors.append(
                f"Missing .svg file in python/nodes/icons\n" f"Expected: At least one .svg file in {icons_path}"
            )

    def _validate_python_tests(self, python_path: Path) -> None:
        """Validate the python/tests folder if it exists.

        Args:
            python_path: Path to the python directory.
        """
        tests_path = python_path / "tests"
        if not tests_path.exists():
            return

        if not (tests_path / "__init__.py").exists():
            self.errors.append(f"Missing __init__.py in python/tests\nExpected: {tests_path}/__init__.py")

        # Verify test file naming convention
        for file_path in tests_path.glob("*.py"):
            if file_path.name not in ("__init__.py", "common.py") and not file_path.name.startswith("test_"):
                self.errors.append(
                    f"Invalid test file name: {file_path.name}\n"
                    "Test files must start with 'test_' (except for __init__.py and common.py)"
                )

    def validate_file_naming(self) -> None:
        """Validate C++ and header file naming conventions."""
        for file_path in self.extension_path.rglob("*"):
            # Skip files in ignored folders
            relative_path = file_path.relative_to(self.extension_path)
            folder_name = relative_path.parts[0] if relative_path.parts else ""
            if folder_name in self.ignored_folders:
                continue

            if file_path.is_file() and file_path.suffix in (".cpp", ".h"):
                self._validate_cpp_file_naming(file_path)

    def _validate_cpp_file_naming(self, file_path: Path) -> None:
        """Validate naming conventions for C++ files.

        Args:
            file_path: Path to the C++ file to validate.
        """
        if not file_path.stem[0].isupper():
            self.errors.append(
                f"Invalid PascalCase naming: {file_path}\n"
                "C++ source and header files must use PascalCase naming convention"
            )

        if file_path.suffix == ".h":
            self._validate_header_file_content(file_path)
        elif file_path.suffix == ".cpp":
            self._validate_cpp_file_content(file_path)

    def _validate_header_file_content(self, file_path: Path) -> None:
        """Validate content-based requirements for header files.

        Args:
            file_path: Path to the header file to validate.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                if "CARB_PLUGIN_INTERFACE" in content and not file_path.stem.startswith("I"):
                    self.errors.append(
                        f"Invalid interface naming: {file_path}\n"
                        "Header files containing CARB_PLUGIN_INTERFACE must start with a capital 'I'"
                    )
        except Exception as e:
            self.warnings.append(f"Could not read file {file_path} to check for CARB_PLUGIN_INTERFACE: {e}")

    def _validate_cpp_file_content(self, file_path: Path) -> None:
        """Validate content-based requirements for C++ source files.

        Args:
            file_path: Path to the C++ file to validate.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                if "CARB_PLUGIN_IMPL" in content and file_path.name != "PluginInterface.cpp":
                    self.errors.append(
                        f"Invalid plugin implementation file name: {file_path}\n"
                        "Files containing CARB_PLUGIN_IMPL must be named PluginInterface.cpp"
                    )
        except Exception as e:
            self.warnings.append(f"Could not read file {file_path} to check for CARB_PLUGIN_IMPL: {e}")

    def validate_premake(self) -> None:
        """Validate the presence of premake5.lua file."""
        premake_path = self.extension_path / "premake5.lua"
        if not premake_path.exists():
            self.errors.append(f"Missing required premake5.lua file\nExpected: {premake_path}")

    def _get_pascal_case_name(self) -> str:
        """Convert extension name to PascalCase.

        Returns:
            The extension name in PascalCase format.
        """
        name_parts = self.extension_name.replace(".", "_").split("_")
        return "".join(part.capitalize() for part in name_parts)

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Run all validation checks on the extension.

        Returns:
            A tuple containing:
            - bool: True if validation passed, False otherwise
            - List[str]: List of error messages
            - List[str]: List of warning messages
        """
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


def validate_extension(path: str) -> bool:
    """Validate a single extension and print results.

    Args:
        path: Path to the extension directory.

    Returns:
        True if the extension is valid, False otherwise.
    """
    validator = ExtensionValidator(path)
    is_valid, errors, warnings = validator.validate()

    if is_valid:
        print(colorize(f"✓ Extension at {path} is valid!", Colors.GREEN + Colors.BOLD))
    else:
        print(colorize(f"✗ Extension at {path} has the following errors:", Colors.RED + Colors.BOLD))
        print_messages(errors, Colors.RED)

    # Print warnings if any
    if warnings:
        print(colorize("\nWarnings:", Colors.YELLOW + Colors.BOLD))
        print_messages(warnings, Colors.YELLOW)

    return is_valid


def validate_extensions_in_directory(
    directory_path: str, recursive: bool = False, ignored_extensions: list[str] | None = None
) -> bool:
    """Validate all extensions in a directory.

    Args:
        directory_path: Path to the directory containing extensions.
        recursive: Whether to search recursively for extensions.
        ignored_extensions: List of extension names to ignore during validation.

    Returns:
        True if all extensions are valid, False otherwise.
    """
    directory = Path(directory_path)
    if not directory.exists():
        print(colorize(f"Directory {directory_path} does not exist.", Colors.RED))
        return False

    ignored_extensions = ignored_extensions or []
    all_valid = True
    valid_count = 0
    invalid_count = 0
    ignored_count = 0

    # Find extensions based on recursive flag
    pattern = "**/isaacsim.*" if recursive else "isaacsim.*"
    extension_paths = [p for p in directory.glob(pattern) if p.is_dir()]

    for path in extension_paths:
        # Check if this extension should be ignored
        if path.name in ignored_extensions:
            print(colorize(f"\nSkipping ignored extension: {path.name}", Colors.YELLOW))
            ignored_count += 1
            continue

        print(colorize(f"\nValidating extension: {path}", Colors.CYAN + Colors.BOLD))
        if validate_extension(str(path)):
            valid_count += 1
        else:
            invalid_count += 1
            all_valid = False

    # Print summary
    total_count = len(extension_paths)
    print(colorize("\n=== Validation Summary ===", Colors.BOLD))
    print(f"Total extensions found: {colorize(str(total_count), Colors.BOLD)}")
    print(f"Ignored extensions: {colorize(str(ignored_count), Colors.YELLOW)}")
    print(f"Valid extensions: {colorize(str(valid_count), Colors.GREEN)}")
    print(f"Invalid extensions: {colorize(str(invalid_count), Colors.RED)}")

    if all_valid:
        print(colorize("\n✓ All non-ignored extensions are valid!", Colors.GREEN + Colors.BOLD))
    else:
        print(colorize(f"\n✗ {invalid_count} extension(s) have validation errors.", Colors.RED + Colors.BOLD))

    return all_valid


def setup_repo_tool(parser: argparse.ArgumentParser, config: dict[str, Any]) -> Callable[..., int]:
    """Setup the repo tool with command-line arguments.

    Args:
        parser: ArgumentParser to configure.
        config: Configuration dictionary.

    Returns:
        The run_tool function to execute the tool.
    """
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


def run_tool(args: argparse.Namespace, config: dict[str, Any]) -> int:
    """Run the extension structure validation tool.

    Args:
        args: Parsed command-line arguments.
        config: Configuration dictionary.

    Returns:
        0 if validation passed, 1 otherwise.
    """
    # Set color mode based on arguments
    if hasattr(args, "no_color") and args.no_color:
        os.environ["NO_COLOR"] = "1"

    # Get the list of extensions to ignore
    ignored_extensions = getattr(args, "ignored_extensions", [])

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
    source_dir = getattr(args, "source_dir", "${root}/source/extensions")
    source_dir = source_dir.replace("${root}", config.get("root", "."))
    recursive = getattr(args, "recursive", False)

    print(colorize(f"Validating extensions in {source_dir}", Colors.CYAN + Colors.BOLD))

    all_valid = validate_extensions_in_directory(source_dir, recursive, ignored_extensions)
    return 0 if all_valid else 1


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(
        description="Validate Isaac Sim extension structure",
    )
    _repo_root = Path(__file__).resolve().parent.parent.parent.parent
    _config: dict[str, Any] = {"root": str(_repo_root)}
    _run = setup_repo_tool(_parser, _config)
    _args = _parser.parse_args()
    sys.exit(_run(_args, _config))
