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

"""
Script to validate that all Python packages defined in pip*.toml files are actually used in the codebase.

This tool analyzes pip*.toml files in the deps/ directory and checks if the Python packages
listed there are actually imported and used in the Python source code. It helps identify
potentially unused dependencies that can be removed to reduce package bloat.

Usage Examples:
    # Basic validation (auto-detects _build/linux-x86_64/release/python.sh, excludes test files)
    python tools/isaac/validate_pip_dependencies.py

    # Use specific Python interpreter (e.g., the build environment)
    _build/linux-x86_64/release/python.sh tools/isaac/validate_pip_dependencies.py

    # Or explicitly specify the python path
    python tools/isaac/validate_pip_dependencies.py --python-path _build/linux-x86_64/release/python.sh

    # Search only in specific directories (follows symlinks automatically)
    python tools/isaac/validate_pip_dependencies.py --search-dirs source exts

    # Search in build directory (useful for analyzing installed packages)
    python tools/isaac/validate_pip_dependencies.py --search-dirs _build/linux-x86_64/release/

    # Include test files in analysis (normally excluded by default)
    python tools/isaac/validate_pip_dependencies.py --no-default-exclusions

    # Add custom exclusions for demo and benchmark files
    python tools/isaac/validate_pip_dependencies.py --exclude "demo_*.py" "benchmark/*.py" "scripts/*.py"

    # Show all imports found in the codebase
    python tools/isaac/validate_pip_dependencies.py --show-imports

    # Save results to JSON for programmatic analysis
    python tools/isaac/validate_pip_dependencies.py --output-json results.json

    # Disable pipdeptree integration (show all unused packages including dependencies)
    python tools/isaac/validate_pip_dependencies.py --no-pipdeptree

    # Verbose output with detailed logging
    python tools/isaac/validate_pip_dependencies.py --verbose

Features:
    - Parses multiple pip*.toml files automatically
    - Handles package name vs import name differences (e.g., Pillow -> PIL)
    - Uses AST parsing for accurate import detection
    - Follows symlinks when searching for Python files (useful for build directories)
    - Integrates with pipdeptree to filter out transitive dependencies
    - Shows which files import each package for verification
    - Automatically excludes test files by default (test_*.py, tests/*, etc.)
    - Supports custom exclusion patterns for non-production code
    - Identifies runtime dependencies that aren't directly imported
    - Supports JSON output for automated analysis with file locations
    - Provides detailed usage statistics and import tracking

Note: This analysis may have false positives for packages that are:
    - Used only at runtime (like CUDA libraries)
    - Imported dynamically using importlib
    - Dependencies of other packages (filtered out with pipdeptree integration)
    - Used through complex import structures
"""

import argparse
import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        print("Error: Neither tomli nor tomllib is available. Please install tomli: pip install tomli")
        sys.exit(1)


class PipDependencyValidator:
    def __init__(
        self,
        root_dir: str,
        verbose: bool = False,
        use_pipdeptree: bool = True,
        python_path: Optional[str] = None,
        exclusion_patterns: Optional[List[str]] = None,
    ):
        self.root_dir = Path(root_dir)
        self.verbose = verbose
        self.use_pipdeptree = use_pipdeptree
        self.python_path = python_path or self._find_python_path()
        self.dependency_graph = {}  # package_name -> set of packages that depend on it
        self.reverse_dependency_graph = {}  # package_name -> set of its dependencies

        # Default exclusion patterns for test files and common non-production code
        default_exclusions = [
            "test_*_archive.py",
            "*omni.isaac.core_archive*",
            "*omni.isaac.ml_archive*",
            "*omni.pip.compute*",
            "*omni.pip.cloud*",
        ]

        self.exclusion_patterns = default_exclusions + (exclusion_patterns or [])

        # Common mappings where package name != import name
        self.package_to_import_mapping = {
            # Image processing
            "pillow": ["PIL"],
            "opencv-python": ["cv2"],
            "opencv-python-headless": ["cv2"],
            "opencv-contrib-python": ["cv2"],
            # Scientific computing
            "scikit-learn": ["sklearn"],
            "scikit-image": ["skimage"],
            "python-dateutil": ["dateutil"],
            "pyyaml": ["yaml"],
            "msgpack-python": ["msgpack"],
            "python-socketio": ["socketio"],
            # Web frameworks
            "beautifulsoup4": ["bs4"],
            "markdown": ["markdown"],
            "markupsafe": ["markupsafe"],
            # Async/Networking
            "aiohttp": ["aiohttp"],
            "requests": ["requests"],
            "urllib3": ["urllib3"],
            # Data processing
            "protobuf": ["google.protobuf", "google"],
            # ML/AI packages
            "torch": ["torch"],
            "torchvision": ["torchvision"],
            "torchaudio": ["torchaudio"],
            "tensorflow": ["tensorflow", "tf"],
            "numpy": ["numpy", "np"],
            "scipy": ["scipy"],
            "matplotlib": ["matplotlib", "mpl_toolkits"],
            # NVIDIA packages
            "nvidia-cublas-cu12": [],  # These are typically not directly imported
            "nvidia-cuda-cupti-cu12": [],
            "nvidia-cuda-nvrtc-cu12": [],
            "nvidia-cuda-runtime-cu12": [],
            "nvidia-cudnn-cu12": [],
            "nvidia-cufft-cu12": [],
            "nvidia-cufile-cu12": [],
            "nvidia-curand-cu12": [],
            "nvidia-cusolver-cu12": [],
            "nvidia-cusparse-cu12": [],
            "nvidia-cusparselt-cu12": [],
            "nvidia-nccl-cu12": [],
            "nvidia-nvjitlink-cu12": [],
            "nvidia-nvtx-cu12": [],
            # Development tools
            "setuptools": ["setuptools", "pkg_resources"],
            "setuptools-scm": ["setuptools_scm"],
            "wheel": ["wheel"],
            "pip": ["pip"],
            # Other common packages
            "six": ["six"],
            "typing-extensions": ["typing_extensions"],
            "python-dateutil": ["dateutil"],
            "pytz": ["pytz"],
            "certifi": ["certifi"],
            "charset-normalizer": ["charset_normalizer"],
            "idna": ["idna"],
            "urllib3": ["urllib3"],
            "packaging": ["packaging"],
            "filelock": ["filelock"],
            "fsspec": ["fsspec"],
            "mpmath": ["mpmath"],
            "networkx": ["networkx"],
            "sympy": ["sympy"],
            "cycler": ["cycler"],
            "kiwisolver": ["kiwisolver"],
            "pyparsing": ["pyparsing"],
            "fonttools": ["fonttools"],
            "contourpy": ["contourpy"],
            "llvmlite": ["llvmlite"],
            "numba": ["numba"],
            "markupsafe": ["markupsafe"],
            "nest-asyncio": ["nest_asyncio"],
            "pint": ["pint"],
            "gunicorn": ["gunicorn"],
            "osqp": ["osqp"],
            "qdldl": ["qdldl"],
            "tornado": ["tornado"],
            "pyperclip": ["pyperclip"],
            "imageio": ["imageio"],
            "trimesh": ["trimesh"],
            "rtree": ["rtree"],
            "lxml": ["lxml", "lxml.etree"],
            "nvidia-lula-no-cuda": ["lula", "nvidia_lula"],
            # SRL packages
            "nvidia-srl-base": ["srl", "nvidia_srl_base", "nvidia.srl", "nvidia.srl.base"],
            "nvidia-srl-math": ["srl", "nvidia_srl_math", "nvidia.srl", "nvidia.srl.math"],
            "nvidia-srl-usd": ["srl", "nvidia_srl_usd", "nvidia.srl", "nvidia.srl.usd"],
            "nvidia-srl-usd-to-urdf": ["srl", "nvidia_srl_usd_to_urdf", "nvidia.srl", "nvidia.srl.usd_to_urdf"],
            # Cloud packages
            "boto3": ["boto3", "botocore"],
            "botocore": ["botocore"],
            "s3transfer": ["s3transfer"],
            "azure-storage-blob": ["azure.storage.blob", "azure"],
            "azure-identity": ["azure.identity", "azure"],
            "azure-core": ["azure.core", "azure"],
            "msal": ["msal"],
            "msal-extensions": ["msal_extensions"],
            "portalocker": ["portalocker"],
            "jmespath": ["jmespath"],
            "isodate": ["isodate"],
            "cryptography": ["cryptography"],
            "oauthlib": ["oauthlib"],
            "requests-oauthlib": ["requests_oauthlib"],
            "pywin32": ["win32api", "win32con", "win32gui", "pywintypes"],  # Windows only
        }

    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"DEBUG: {message}")

    def _find_python_path(self) -> str:
        """Find the appropriate Python interpreter to use."""
        # Try the build-specific python.sh first
        python_sh = self.root_dir / "_build" / "linux-x86_64" / "release" / "python.sh"
        if python_sh.exists():
            self.log(f"Found build-specific Python: {python_sh}")
            return str(python_sh)

        # Fallback to system python
        self.log("Using system python as fallback")
        return "python"

    def is_file_excluded(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on exclusion patterns."""
        # Convert to relative path from root for consistent pattern matching
        try:
            relative_path = file_path.relative_to(self.root_dir)
        except ValueError:
            # File is not under root directory, use absolute path
            relative_path = file_path

        path_str = str(relative_path).replace(os.sep, "/")  # Normalize path separators

        for pattern in self.exclusion_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also check just the filename
            if fnmatch.fnmatch(file_path.name, pattern):
                return True

        return False

    def check_pipdeptree_available(self) -> bool:
        """Check if pipdeptree is available."""
        try:
            # Use the specific python interpreter to check for pipdeptree
            result = subprocess.run(
                [self.python_path, "-m", "pipdeptree", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if result.returncode == 0:
                self.log(f"pipdeptree version: {result.stdout.strip()}")
                self.log(f"Using Python interpreter: {self.python_path}")
                return True
            else:
                self.log(f"pipdeptree command failed with return code {result.returncode}")
                return False
        except FileNotFoundError:
            self.log(f"Python interpreter not found: {self.python_path}")
            return False
        except Exception as e:
            self.log(f"Error checking pipdeptree: {e}")
            return False

    def get_dependency_tree(self) -> bool:
        """Get dependency tree using pipdeptree and build dependency graphs."""
        if not self.use_pipdeptree:
            return False

        if not self.check_pipdeptree_available():
            print("Warning: pipdeptree not available in the target Python environment.")
            print(f"Install with: {self.python_path} -m pip install pipdeptree")
            print("Dependency filtering will be disabled.")
            return False

        try:
            # Get dependency tree in JSON format using the specific python interpreter
            result = subprocess.run(
                [self.python_path, "-m", "pipdeptree", "--json-tree"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if result.returncode != 0:
                self.log(f"pipdeptree failed with return code {result.returncode}")
                return False

            if not result.stdout.strip():
                self.log("pipdeptree returned empty output")
                return False

            # pipdeptree may output warnings before the JSON, find the JSON part
            json_start = result.stdout.find("[")
            if json_start == -1:
                self.log("No JSON array found in pipdeptree output")
                return False

            json_content = result.stdout[json_start:]
            dependency_data = json.loads(json_content)
            self.log(f"Loaded dependency tree with {len(dependency_data)} top-level packages")

            # Build dependency graphs
            self.dependency_graph = {}
            self.reverse_dependency_graph = {}

            def process_package(pkg_info, parent_name=None):
                """Recursively process package dependency information."""
                pkg_name = pkg_info["package_name"].lower()

                # Initialize if not exists
                if pkg_name not in self.dependency_graph:
                    self.dependency_graph[pkg_name] = set()
                if pkg_name not in self.reverse_dependency_graph:
                    self.reverse_dependency_graph[pkg_name] = set()

                # If this package has a parent, record the dependency relationship
                if parent_name:
                    parent_name = parent_name.lower()
                    self.dependency_graph[pkg_name].add(parent_name)
                    if parent_name not in self.reverse_dependency_graph:
                        self.reverse_dependency_graph[parent_name] = set()
                    self.reverse_dependency_graph[parent_name].add(pkg_name)

                # Process dependencies recursively
                for dep in pkg_info.get("dependencies", []):
                    process_package(dep, pkg_name)

            # Process all top-level packages
            for pkg_info in dependency_data:
                process_package(pkg_info)

            self.log(f"Built dependency graph with {len(self.dependency_graph)} packages")
            return True

        except Exception as e:
            self.log(f"Error getting dependency tree: {e}")
            return False

    def is_dependency_of_used_package(self, package_name: str, used_packages: Set[str]) -> Tuple[bool, Optional[str]]:
        """Check if a package is a dependency of any used package."""
        if not self.dependency_graph:
            return False, None

        package_name = package_name.lower()

        # Check if this package is a dependency of any used package
        if package_name in self.dependency_graph:
            dependents = self.dependency_graph[package_name]
            for dependent in dependents:
                if dependent in used_packages:
                    return True, dependent
                # Check transitively - if the dependent is also a dependency of a used package
                is_transitive, transitive_parent = self.is_dependency_of_used_package(dependent, used_packages)
                if is_transitive:
                    return True, transitive_parent

        return False, None

    def extract_package_name(self, package_spec: str) -> str:
        """Extract package name from package specification (e.g., 'numpy==1.23.5' -> 'numpy')."""
        # Remove version specifiers
        package_name = re.split(r"[=<>!~]", package_spec)[0].strip()

        # Handle extra requirements like 'boto3[crt]==1.36.1' -> 'boto3'
        if "[" in package_name:
            package_name = package_name.split("[")[0]

        return package_name.lower()

    def get_import_names(self, package_name: str) -> List[str]:
        """Get possible import names for a package."""
        package_name = package_name.lower()

        if package_name in self.package_to_import_mapping:
            return self.package_to_import_mapping[package_name]

        # Default: try the package name itself, converting hyphens to underscores
        default_import = package_name.replace("-", "_")
        return [default_import, package_name]

    def parse_pip_toml_files(self) -> Dict[str, List[str]]:
        """Parse all pip*.toml files and extract package dependencies."""
        deps_dir = self.root_dir / "deps"
        packages_by_file = {}

        if not deps_dir.exists():
            print(f"Error: deps directory not found at {deps_dir}")
            return packages_by_file

        pip_toml_files = list(deps_dir.glob("pip*.toml"))
        self.log(f"Found {len(pip_toml_files)} pip*.toml files")

        for toml_file in pip_toml_files:
            self.log(f"Processing {toml_file}")
            packages = []

            try:
                with open(toml_file, "rb") as f:
                    toml_data = tomli.load(f)

                # Extract packages from all dependency sections
                for dependency in toml_data.get("dependency", []):
                    for package_spec in dependency.get("packages", []):
                        package_name = self.extract_package_name(package_spec)
                        packages.append(package_name)
                        self.log(f"  Found package: {package_name} (from {package_spec})")

                packages_by_file[str(toml_file.relative_to(self.root_dir))] = sorted(set(packages))

            except Exception as e:
                print(f"Error parsing {toml_file}: {e}")

        return packages_by_file

    def find_python_files(self, search_dirs: List[str]) -> List[Path]:
        """Find all Python files in the specified directories, following symlinks."""
        python_files = []

        for search_dir in search_dirs:
            search_path = self.root_dir / search_dir
            if not search_path.exists():
                self.log(f"Search directory not found: {search_path}")
                continue

            self.log(f"Searching for Python files in {search_path} (following symlinks)")

            # Use os.walk to follow symlinks when searching for Python files
            for root, dirs, files in os.walk(str(search_path), followlinks=True):
                for file in files:
                    if file.endswith(".py"):
                        py_file = Path(root) / file
                        python_files.append(py_file)

        self.log(f"Found {len(python_files)} Python files (following symlinks)")
        return python_files

    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """Extract import names from a Python file."""
        imports = set()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse the AST to extract imports
            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Handle 'import package' and 'import package.submodule'
                            top_level = alias.name.split(".")[0]
                            imports.add(top_level)

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Handle 'from package import ...'
                            top_level = node.module.split(".")[0]
                            imports.add(top_level)

            except SyntaxError:
                # If AST parsing fails, fall back to regex
                self.log(f"AST parsing failed for {file_path}, using regex fallback")
                imports.update(self.extract_imports_regex(content))

        except Exception as e:
            self.log(f"Error reading {file_path}: {e}")

        return imports

    def extract_imports_regex(self, content: str) -> Set[str]:
        """Fallback method to extract imports using regex."""
        imports = set()

        # Match 'import package' and 'from package import ...'
        import_patterns = [
            r"^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
            r"^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import",
        ]

        for line in content.splitlines():
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    top_level = module_name.split(".")[0]
                    imports.add(top_level)

        return imports

    def find_used_packages(self, search_dirs: List[str]) -> Tuple[Set[str], Dict[str, str]]:
        """Find all packages that are actually imported in the codebase.

        Returns:
            Tuple of (all_imports_set, import_to_file_mapping)
        """
        python_files = self.find_python_files(search_dirs)
        all_imports = set()
        import_to_file = {}  # import_name -> first file that imports it
        excluded_files_count = 0

        for py_file in python_files:
            # Skip excluded files (like test files)
            if self.is_file_excluded(py_file):
                excluded_files_count += 1
                self.log(f"Excluding file: {py_file.relative_to(self.root_dir)}")
                continue

            imports = self.extract_imports_from_file(py_file)
            for import_name in imports:
                all_imports.add(import_name)
                # Record the first file that imports this package
                if import_name not in import_to_file:
                    relative_path = str(py_file.relative_to(self.root_dir))
                    import_to_file[import_name] = relative_path

        self.log(f"Found {len(python_files)} Python files, excluded {excluded_files_count} files")
        self.log(f"Found {len(all_imports)} unique top-level imports")
        self.log(f"Tracking import locations for {len(import_to_file)} imports")
        return all_imports, import_to_file

    def validate_dependencies(
        self, search_dirs: List[str]
    ) -> Tuple[Dict[str, Dict[str, List]], Set[str], Dict[str, str]]:
        """Validate pip dependencies against actual usage."""
        # Get dependency tree information if enabled
        has_dependency_tree = self.get_dependency_tree()

        # Parse pip*.toml files
        packages_by_file = self.parse_pip_toml_files()

        # Find all imports used in the codebase
        used_imports, import_to_file = self.find_used_packages(search_dirs)

        # Build set of used package names (convert from import names to package names)
        used_package_names = set()
        for toml_file, packages in packages_by_file.items():
            for package in packages:
                import_names = self.get_import_names(package)
                for import_name in import_names:
                    if import_name in used_imports:
                        used_package_names.add(package.lower())
                        break

        # Analyze each file
        results = {}

        for toml_file, packages in packages_by_file.items():
            unused_packages = []
            used_packages = []
            dependency_packages = []  # packages that are dependencies of used packages

            for package in packages:
                import_names = self.get_import_names(package)

                # Check if any of the possible import names are used
                is_used = False
                matched_import = None
                import_file = None
                for import_name in import_names:
                    if import_name in used_imports:
                        is_used = True
                        matched_import = import_name
                        import_file = import_to_file.get(import_name, "unknown")
                        break

                if is_used:
                    used_packages.append((package, matched_import, import_file))
                    self.log(f"Package {package} is USED (matched import: {matched_import} in {import_file})")
                else:
                    # Check if this package is a dependency of a used package
                    if has_dependency_tree:
                        is_dependency, dependent_package = self.is_dependency_of_used_package(
                            package, used_package_names
                        )
                        if is_dependency:
                            dependency_packages.append((package, dependent_package))
                            self.log(f"Package {package} is a DEPENDENCY of used package: {dependent_package}")
                        else:
                            unused_packages.append(package)
                            self.log(f"Package {package} is UNUSED (import names: {import_names})")
                    else:
                        unused_packages.append(package)
                        self.log(f"Package {package} is UNUSED (import names: {import_names})")

            results[toml_file] = {
                "used": used_packages,
                "unused": unused_packages,
                "dependencies": dependency_packages,
            }

        return results, used_imports, import_to_file

    def print_results(self, results: Dict[str, Dict[str, List]], all_imports: Set[str], show_imports: bool = False):
        """Print validation results."""
        total_packages = 0
        total_unused = 0
        total_dependencies = 0
        has_dependency_info = any(
            "dependencies" in file_results and len(file_results["dependencies"]) > 0
            for file_results in results.values()
        )

        for toml_file, file_results in results.items():
            used_packages = file_results["used"]
            unused_packages = file_results["unused"]
            dependency_packages = file_results.get("dependencies", [])

            total_packages += len(used_packages) + len(unused_packages) + len(dependency_packages)
            total_unused += len(unused_packages)
            total_dependencies += len(dependency_packages)

            print(f"\n=== {toml_file} ===")
            print(f"Total packages: {len(used_packages) + len(unused_packages) + len(dependency_packages)}")
            print(f"Used packages: {len(used_packages)}")
            if has_dependency_info:
                print(f"Dependency packages: {len(dependency_packages)}")
            print(f"Unused packages: {len(unused_packages)}")

            if unused_packages:
                print("\nUnused packages:")
                for package in sorted(unused_packages):
                    import_names = self.get_import_names(package)
                    if import_names:
                        print(f"  - {package} (would import as: {', '.join(import_names)})")
                    else:
                        print(f"  - {package} (runtime dependency, not directly imported)")

            if used_packages and len(used_packages) <= 10:  # Show details for reasonable number of packages
                print("\nUsed packages:")
                for package, matched_import, import_file in sorted(used_packages):
                    print(f"  + {package} (imported as: {matched_import} in {import_file})")
            elif used_packages and len(used_packages) > 10:
                print(f"\nUsed packages: ({len(used_packages)} packages - run with --verbose to see all)")

            if dependency_packages:
                print("\nDependency packages (used transitively):")
                for package, dependent in sorted(dependency_packages):
                    print(f"  ~ {package} (dependency of: {dependent})")

            if self.verbose and used_packages and len(used_packages) > 10:
                print("\nAll used packages:")
                for package, matched_import, import_file in sorted(used_packages):
                    print(f"  + {package} (imported as: {matched_import} in {import_file})")

        if show_imports:
            print(f"\n=== All Imports Found ({len(all_imports)}) ===")
            for imp in sorted(all_imports):
                print(f"  {imp}")

        print(f"\n=== Summary ===")
        print(f"Total packages analyzed: {total_packages}")
        if has_dependency_info:
            print(f"Dependency packages: {total_dependencies}")
        print(f"Unused packages: {total_unused}")
        used_packages_count = total_packages - total_unused - total_dependencies
        print(f"Directly used packages: {used_packages_count}")
        effective_usage_rate = (
            ((used_packages_count + total_dependencies) / total_packages * 100) if total_packages > 0 else 0
        )
        print(f"Usage rate (including dependencies): {effective_usage_rate:.1f}%")

        if total_unused > 0:
            print(f"\nFound {total_unused} potentially unused packages.")
            if has_dependency_info:
                print("Transitive dependencies have been filtered out using pipdeptree.")
            print("Note: This analysis may have false positives for:")
            print("  - Packages used only at runtime")
            print("  - Packages imported dynamically")
            print("  - Packages with complex import structures")
            if not has_dependency_info:
                print("  - Runtime dependencies of other packages")
                print("  Install pipdeptree to filter out transitive dependencies: pip install pipdeptree")

    def save_results_json(
        self,
        results: Dict[str, Dict[str, List]],
        all_imports: Set[str],
        import_to_file: Dict[str, str],
        output_file: str,
    ):
        """Save results to a JSON file."""
        # Convert tuples to dictionaries for JSON serialization
        json_results = {}
        for toml_file, file_results in results.items():
            used_packages_list = []
            for package, matched_import, import_file in file_results["used"]:
                used_packages_list.append(
                    {
                        "package": package,
                        "matched_import": matched_import,
                        "import_file": import_file,
                        "possible_imports": self.get_import_names(package),
                    }
                )

            unused_packages_list = []
            for package in file_results["unused"]:
                unused_packages_list.append({"package": package, "possible_imports": self.get_import_names(package)})

            dependency_packages_list = []
            if "dependencies" in file_results:
                for package, dependent in file_results["dependencies"]:
                    dependency_packages_list.append(
                        {
                            "package": package,
                            "dependent_package": dependent,
                            "possible_imports": self.get_import_names(package),
                        }
                    )

            json_results[toml_file] = {
                "used": used_packages_list,
                "unused": unused_packages_list,
                "dependencies": dependency_packages_list,
            }

        total_dependencies = sum(len(f.get("dependencies", [])) for f in results.values())

        output_data = {
            "results": json_results,
            "all_imports": sorted(list(all_imports)),
            "import_to_file": import_to_file,
            "summary": {
                "total_packages": sum(
                    len(f["used"]) + len(f["unused"]) + len(f.get("dependencies", [])) for f in results.values()
                ),
                "total_unused": sum(len(f["unused"]) for f in results.values()),
                "total_dependencies": total_dependencies,
                "total_directly_used": sum(len(f["used"]) for f in results.values()),
                "total_imports_found": len(all_imports),
                "has_dependency_info": total_dependencies > 0 or any("dependencies" in f for f in results.values()),
            },
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate that Python packages in pip*.toml files are actually used in the codebase"
    )
    parser.add_argument(
        "--root", type=str, default=".", help="Root directory of the repository (default: current directory)"
    )
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=["_build/linux-x86_64/release", "source", "exts"],
        help="Directories to search for Python files (default: _build/linux-x86_64/release source exts)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--show-imports", action="store_true", help="Show all imports found in the codebase")
    parser.add_argument("--output-json", type=str, help="Write results to a JSON file")
    parser.add_argument(
        "--no-pipdeptree", action="store_true", help="Disable pipdeptree integration for dependency filtering"
    )
    parser.add_argument(
        "--python-path",
        type=str,
        help="Path to Python interpreter to use (default: auto-detect _build/linux-x86_64/release/python.sh)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional file patterns to exclude (e.g., --exclude 'benchmark_*.py' 'demo/*.py')",
    )
    parser.add_argument(
        "--no-default-exclusions", action="store_true", help="Disable default exclusions for test files"
    )

    args = parser.parse_args()

    # Validate root directory
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        print(f"Error: Root directory does not exist: {root_path}")
        return 1

    print(f"Validating pip dependencies in: {root_path}")
    print(f"Searching for Python files in: {', '.join(args.search_dirs)}")

    if not args.no_default_exclusions:
        print("Excluding test files by default (use --no-default-exclusions to include)")
    if args.exclude:
        print(f"Additional exclusions: {', '.join(args.exclude)}")

    # Configure exclusions
    exclusion_patterns = []
    if not args.no_default_exclusions:
        exclusion_patterns = None  # Use default exclusions
    if args.exclude:
        exclusion_patterns = (exclusion_patterns or []) + args.exclude

    use_pipdeptree = not args.no_pipdeptree
    validator = PipDependencyValidator(
        str(root_path),
        verbose=args.verbose,
        use_pipdeptree=use_pipdeptree,
        python_path=args.python_path,
        exclusion_patterns=exclusion_patterns,
    )
    results, all_imports, import_to_file = validator.validate_dependencies(args.search_dirs)
    validator.print_results(results, all_imports, show_imports=args.show_imports)

    if args.output_json:
        validator.save_results_json(results, all_imports, import_to_file, args.output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
