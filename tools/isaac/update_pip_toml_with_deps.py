#!/usr/bin/env python3
"""Analyze pip*.toml usage and update SWIPAT usage comments.

This tool combines package usage analysis, dependency validation, and automatic
updates to pip*.toml usage comments. It can either update from a precomputed JSON
file or analyze the repository and update in a single run.
"""

import argparse
import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        print("Error: Neither tomli nor tomllib is available. Please install tomli: pip install tomli")
        sys.exit(1)


def load_package_info(json_file: str) -> Dict[str, Dict[str, List[str]]]:
    """Load the package info with dependencies from a JSON file.

    Args:
        json_file: Path to the JSON file produced by this tool.

    Returns:
        Dictionary mapping package names to info dicts with extensions and dependencies.
    """
    with open(json_file, "r") as f:
        data = json.load(f)

    package_info = data.get("package_info", data)
    normalized = {}
    for package_name, info in package_info.items():
        normalized[package_name] = {
            "extensions": info.get("extensions", []),
            "dependency_of": info.get("dependency_of", []),
        }
    return normalized


def extract_package_name(package_line: str) -> Optional[str]:
    """Extract package name from a pip.toml package line.

    Args:
        package_line: Line like '"numba==0.59.1",' or '"boto3",'

    Returns:
        Package name in lowercase (e.g., 'numba', 'boto3').
    """
    match = re.search(r'"([^"]+)"', package_line)
    if match:
        package_spec = match.group(1)
        package_name = re.split(r"[=<>!~\[]", package_spec)[0].strip()
        return package_name.lower()
    return None


def update_pip_toml(toml_file: Path, package_info: Dict[str, Dict[str, List[str]]]) -> None:
    """Update a pip.toml file with extension usage and dependency comments.

    Args:
        toml_file: Path to the pip.toml file.
        package_info: Dictionary mapping package names to info dicts with extensions and dependencies.
    """
    with open(toml_file, "r") as f:
        lines = f.readlines()

    sections = []
    current_section_start = None
    current_section_packages = []

    for i, line in enumerate(lines):
        if "[[dependency]]" in line:
            if current_section_start is not None and current_section_packages:
                max_len = max(len(pkg) for pkg in current_section_packages)
                sections.append((current_section_start, i - 1, max_len))
            current_section_start = i
            current_section_packages = []

        if '"' in line and ("SWIPAT filed under:" in line or "SWIPAT:" in line):
            match = re.match(r'^(\s*"[^"]+",?\s*)', line)
            if match:
                package_part = match.group(1).rstrip()
                current_section_packages.append(package_part)

    if current_section_start is not None and current_section_packages:
        max_len = max(len(pkg) for pkg in current_section_packages)
        sections.append((current_section_start, len(lines) - 1, max_len))

    line_to_max_len = {}
    for start_idx, end_idx, max_len in sections:
        for i in range(start_idx, end_idx + 1):
            line_to_max_len[i] = max_len

    updated_lines = []
    for i, line in enumerate(lines):
        updated_line = line

        if '"' in line and ("SWIPAT filed under:" in line or "SWIPAT:" in line):
            package_name = extract_package_name(line)

            if package_name and package_name in package_info:
                info = package_info[package_name]
                extensions = info["extensions"]
                dependency_of = info["dependency_of"]

                match = re.match(r'^(\s*"[^"]+",?\s*)', line)
                if match:
                    package_part = match.group(1).rstrip()

                    swipat_comment = None
                    if "SWIPAT filed under:" in line:
                        swipat_match = re.search(r"# SWIPAT filed under: (https?://[^\s#]+)", line)
                        if swipat_match:
                            swipat_comment = f"# SWIPAT filed under: {swipat_match.group(1)}"
                    elif "SWIPAT:" in line:
                        swipat_match = re.search(r"# SWIPAT: (https?://[^\s#]+)", line)
                        if swipat_match:
                            swipat_comment = f"# SWIPAT filed under: {swipat_match.group(1)}"

                    if swipat_comment:
                        max_package_len = line_to_max_len.get(i, len(package_part))
                        padding = " " * (max_package_len - len(package_part) + 1)

                        if extensions:
                            ext_list = ", ".join(sorted(extensions))
                            usage_comment = f"# Used by: {ext_list}"
                        elif dependency_of:
                            dep_list = ", ".join(sorted(dependency_of))
                            usage_comment = f"# Used by: (dependency of {dep_list})"
                        else:
                            usage_comment = "# Used by: (none found)"

                        updated_line = f"{package_part}{padding}{swipat_comment} {usage_comment}\n"

        updated_lines.append(updated_line)

    with open(toml_file, "w") as f:
        f.writelines(updated_lines)

    print(f"Updated {toml_file}")


def update_pip_toml_files(deps_dir: Path, package_info: Dict[str, Dict[str, List[str]]]) -> List[Path]:
    """Update all pip*.toml files in a directory.

    Args:
        deps_dir: Directory containing pip*.toml files.
        package_info: Dictionary mapping package names to info dicts with extensions and dependencies.

    Returns:
        List of updated toml file paths.
    """
    toml_files = sorted(deps_dir.glob("pip*.toml"))
    if not toml_files:
        print(f"\nNo pip*.toml files found in {deps_dir}")
        return []

    print(f"\nFound {len(toml_files)} pip*.toml file(s) to update:")
    for toml_file in toml_files:
        print(f"  - {toml_file.name}")

    print()
    for toml_file in toml_files:
        update_pip_toml(toml_file, package_info)

    return toml_files


class PipDependencyValidator:
    """Validates that Python packages in pip*.toml files are actually used in the codebase."""

    def __init__(
        self,
        root_dir: str,
        verbose: bool = False,
        use_pipdeptree: bool = True,
        python_path: Optional[str] = None,
        exclusion_patterns: Optional[List[str]] = None,
    ):
        """Initialize the PipDependencyValidator.

        Args:
            root_dir: Root directory of the repository to analyze.
            verbose: Enable verbose debug output.
            use_pipdeptree: Enable pipdeptree integration for dependency tree analysis.
            python_path: Path to Python interpreter to use. If None, auto-detects.
            exclusion_patterns: Additional file patterns to exclude from analysis.
        """
        self.root_dir = Path(root_dir)
        self.verbose = verbose
        self.use_pipdeptree = use_pipdeptree
        self.python_path = python_path or self._find_python_path()
        self.dependency_graph = {}
        self.reverse_dependency_graph = {}

        default_exclusions = [
            "test_*_archive.py",
            "*omni.isaac.core_archive*",
            "*omni.isaac.ml_archive*",
            "*omni.pip.compute*",
            "*omni.pip.cloud*",
        ]

        self.exclusion_patterns = default_exclusions + (exclusion_patterns or [])

        self.package_to_import_mapping = {
            "pillow": ["PIL"],
            "opencv-python": ["cv2"],
            "opencv-python-headless": ["cv2"],
            "opencv-contrib-python": ["cv2"],
            "scikit-learn": ["sklearn"],
            "scikit-image": ["skimage"],
            "python-dateutil": ["dateutil"],
            "pyyaml": ["yaml"],
            "msgpack-python": ["msgpack"],
            "python-socketio": ["socketio"],
            "beautifulsoup4": ["bs4"],
            "markdown": ["markdown"],
            "aiohttp": ["aiohttp"],
            "requests": ["requests"],
            "urllib3": ["urllib3"],
            "protobuf": ["google.protobuf", "google"],
            "torch": ["torch"],
            "torchvision": ["torchvision"],
            "torchaudio": ["torchaudio"],
            "tensorflow": ["tensorflow", "tf"],
            "numpy": ["numpy", "np"],
            "scipy": ["scipy"],
            "matplotlib": ["matplotlib", "mpl_toolkits"],
            "nvidia-cublas-cu12": [],
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
            "setuptools": ["setuptools", "pkg_resources"],
            "setuptools-scm": ["setuptools_scm"],
            "wheel": ["wheel"],
            "pip": ["pip"],
            "six": ["six"],
            "typing-extensions": ["typing_extensions"],
            "pytz": ["pytz"],
            "certifi": ["certifi"],
            "charset-normalizer": ["charset_normalizer"],
            "idna": ["idna"],
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
            "nest-asyncio": ["nest_asyncio"],
            "osqp": ["osqp"],
            "qdldl": ["qdldl"],
            "pyperclip": ["pyperclip"],
            "imageio": ["imageio"],
            "trimesh": ["trimesh"],
            "rtree": ["rtree"],
            "lxml": ["lxml", "lxml.etree"],
            "nvidia-lula-no-cuda": ["lula", "nvidia_lula"],
            "nvidia-srl-base": ["srl", "nvidia_srl_base", "nvidia.srl", "nvidia.srl.base"],
            "nvidia-srl-math": ["srl", "nvidia_srl_math", "nvidia.srl", "nvidia.srl.math"],
            "nvidia-srl-usd": ["srl", "nvidia_srl_usd", "nvidia.srl", "nvidia.srl.usd"],
            "nvidia-srl-usd-to-urdf": ["srl", "nvidia_srl_usd_to_urdf", "nvidia.srl", "nvidia.srl.usd_to_urdf"],
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
            "pywin32": ["win32api", "win32con", "win32gui", "pywintypes"],
        }

    def log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"DEBUG: {message}")

    def _find_python_path(self) -> str:
        """Find the appropriate Python interpreter to use."""
        python_sh = self.root_dir / "_build" / "linux-x86_64" / "release" / "python.sh"
        if python_sh.exists():
            self.log(f"Found build-specific Python: {python_sh}")
            return str(python_sh)
        self.log("Using system python as fallback")
        return "python"

    def is_file_excluded(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on exclusion patterns."""
        try:
            relative_path = file_path.relative_to(self.root_dir)
        except ValueError:
            relative_path = file_path

        path_str = str(relative_path).replace(os.sep, "/")
        for pattern in self.exclusion_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False

    def check_pipdeptree_available(self) -> bool:
        """Check if pipdeptree is available in the target Python environment."""
        try:
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

            json_start = result.stdout.find("[")
            if json_start == -1:
                self.log("No JSON array found in pipdeptree output")
                return False

            json_content = result.stdout[json_start:]
            dependency_data = json.loads(json_content)
            self.log(f"Loaded dependency tree with {len(dependency_data)} top-level packages")

            self.dependency_graph = {}
            self.reverse_dependency_graph = {}

            def process_package(pkg_info, parent_name=None):
                pkg_name = pkg_info["package_name"].lower()

                if pkg_name not in self.dependency_graph:
                    self.dependency_graph[pkg_name] = set()
                if pkg_name not in self.reverse_dependency_graph:
                    self.reverse_dependency_graph[pkg_name] = set()

                if parent_name:
                    parent_name = parent_name.lower()
                    self.dependency_graph[pkg_name].add(parent_name)
                    if parent_name not in self.reverse_dependency_graph:
                        self.reverse_dependency_graph[parent_name] = set()
                    self.reverse_dependency_graph[parent_name].add(pkg_name)

                for dep in pkg_info.get("dependencies", []):
                    process_package(dep, pkg_name)

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
        if package_name in self.dependency_graph:
            dependents = self.dependency_graph[package_name]
            for dependent in dependents:
                if dependent in used_packages:
                    return True, dependent
                is_transitive, transitive_parent = self.is_dependency_of_used_package(dependent, used_packages)
                if is_transitive:
                    return True, transitive_parent

        return False, None

    def extract_package_name(self, package_spec: str) -> str:
        """Extract package name from package specification."""
        package_name = re.split(r"[=<>!~]", package_spec)[0].strip()
        if "[" in package_name:
            package_name = package_name.split("[")[0]
        return package_name.lower()

    def get_import_names(self, package_name: str) -> List[str]:
        """Get possible import names for a package."""
        package_name = package_name.lower()
        if package_name in self.package_to_import_mapping:
            return self.package_to_import_mapping[package_name]
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
            for root, _, files in os.walk(str(search_path), followlinks=True):
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

            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=SyntaxWarning)
                    tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            top_level = alias.name.split(".")[0]
                            imports.add(top_level)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            top_level = node.module.split(".")[0]
                            imports.add(top_level)

            except SyntaxError:
                self.log(f"AST parsing failed for {file_path}, using regex fallback")
                imports.update(self.extract_imports_regex(content))

        except Exception as e:
            self.log(f"Error reading {file_path}: {e}")

        return imports

    def extract_imports_regex(self, content: str) -> Set[str]:
        """Fallback method to extract imports using regex."""
        imports = set()
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

    def extract_extension_from_path(self, file_path: Path) -> Optional[str]:
        """Extract extension name from a file path."""
        try:
            relative_path = file_path.relative_to(self.root_dir)
        except ValueError:
            return None

        parts = relative_path.parts
        if len(parts) >= 3 and parts[0] == "source" and parts[1] == "extensions":
            return parts[2]

        if "exts" in parts:
            exts_idx = parts.index("exts")
            for i in range(exts_idx + 1, len(parts)):
                candidate = parts[i]
                if not candidate.isdigit():
                    base_name = candidate.split("-")[0]
                    return base_name

        if len(parts) >= 2 and parts[0] == "exts":
            candidate = parts[1]
            if not candidate.isdigit():
                base_name = candidate.split("-")[0]
                return base_name

        return None

    def find_used_packages(self, search_dirs: List[str]) -> Tuple[Set[str], Dict[str, str]]:
        """Find all packages that are actually imported in the codebase."""
        python_files = self.find_python_files(search_dirs)
        all_imports = set()
        import_to_file = {}
        excluded_files_count = 0

        for py_file in python_files:
            if self.is_file_excluded(py_file):
                excluded_files_count += 1
                self.log(f"Excluding file: {py_file.relative_to(self.root_dir)}")
                continue

            imports = self.extract_imports_from_file(py_file)
            for import_name in imports:
                all_imports.add(import_name)
                if import_name not in import_to_file:
                    relative_path = str(py_file.relative_to(self.root_dir))
                    import_to_file[import_name] = relative_path

        self.log(f"Found {len(python_files)} Python files, excluded {excluded_files_count} files")
        self.log(f"Found {len(all_imports)} unique top-level imports")
        self.log(f"Tracking import locations for {len(import_to_file)} imports")
        return all_imports, import_to_file

    def build_package_to_extensions_mapping(self, search_dirs: List[str]) -> Dict[str, Set[str]]:
        """Build a mapping of packages to the extensions that use them."""
        python_files = self.find_python_files(search_dirs)
        import_to_extensions = defaultdict(set)
        excluded_files_count = 0
        files_without_extension = 0

        for py_file in python_files:
            if self.is_file_excluded(py_file):
                excluded_files_count += 1
                self.log(f"Excluding file: {py_file.relative_to(self.root_dir)}")
                continue

            extension_name = self.extract_extension_from_path(py_file)
            if not extension_name:
                files_without_extension += 1
                self.log(f"Could not extract extension from: {py_file.relative_to(self.root_dir)}")
                continue

            if extension_name.isdigit() or len(extension_name) <= 3 and extension_name.replace(".", "").isdigit():
                self.log(
                    f"WARNING: Suspicious extension name '{extension_name}' from path: {py_file.relative_to(self.root_dir)}"
                )

            imports = self.extract_imports_from_file(py_file)
            for import_name in imports:
                import_to_extensions[import_name].add(extension_name)
                self.log(f"Package {import_name} used by extension {extension_name}")

        self.log(f"Found {len(python_files)} Python files, excluded {excluded_files_count} files")
        self.log(f"Files without extension: {files_without_extension}")
        self.log(f"Built mapping for {len(import_to_extensions)} imports across extensions")
        return dict(import_to_extensions)

    def validate_dependencies(
        self, search_dirs: List[str]
    ) -> Tuple[Dict[str, Dict[str, List]], Set[str], Dict[str, str]]:
        """Validate pip dependencies against actual usage."""
        has_dependency_tree = self.get_dependency_tree()
        packages_by_file = self.parse_pip_toml_files()
        used_imports, import_to_file = self.find_used_packages(search_dirs)

        used_package_names = set()
        for packages in packages_by_file.values():
            for package in packages:
                import_names = self.get_import_names(package)
                for import_name in import_names:
                    if import_name in used_imports:
                        used_package_names.add(package.lower())
                        break

        results = {}
        for toml_file, packages in packages_by_file.items():
            unused_packages = []
            used_packages = []
            dependency_packages = []

            for package in packages:
                import_names = self.get_import_names(package)
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

    def analyze_package_extensions(self, search_dirs: List[str]) -> Dict[str, Set[str]]:
        """Analyze which extensions use which pip packages."""
        packages_by_file = self.parse_pip_toml_files()
        all_packages = set()
        for packages in packages_by_file.values():
            all_packages.update(packages)

        import_to_extensions = self.build_package_to_extensions_mapping(search_dirs)
        package_to_extensions = {}

        for package_name in all_packages:
            extensions = set()
            import_names = self.get_import_names(package_name)
            for import_name in import_names:
                if import_name in import_to_extensions:
                    extensions.update(import_to_extensions[import_name])
            package_to_extensions[package_name] = extensions

        return package_to_extensions

    def analyze_package_extensions_with_dependencies(self, search_dirs: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze which extensions use which packages, including transitive dependencies."""
        has_dependency_tree = self.get_dependency_tree()
        packages_by_file = self.parse_pip_toml_files()
        all_packages = set()
        for packages in packages_by_file.values():
            all_packages.update(packages)

        import_to_extensions = self.build_package_to_extensions_mapping(search_dirs)
        package_info = {}

        for package_name in all_packages:
            extensions = set()
            import_names = self.get_import_names(package_name)
            for import_name in import_names:
                if import_name in import_to_extensions:
                    extensions.update(import_to_extensions[import_name])
            package_info[package_name] = {"extensions": extensions, "dependency_of": set()}

        if has_dependency_tree:
            used_packages = {pkg for pkg, info in package_info.items() if info["extensions"]}
            for package_name in all_packages:
                if not package_info[package_name]["extensions"]:
                    package_name_lower = package_name.lower()
                    if package_name_lower in self.dependency_graph:
                        dependents = self.dependency_graph[package_name_lower]
                        for dependent in dependents:
                            if dependent in all_packages:
                                package_info[package_name]["dependency_of"].add(dependent)

        return package_info

    def print_package_extensions(self, package_to_extensions: Dict[str, Set[str]]) -> None:
        """Print package-to-extensions mapping."""
        print("\n=== Package to Extensions Mapping ===\n")
        for package_name in sorted(package_to_extensions.keys()):
            extensions = package_to_extensions[package_name]
            if extensions:
                ext_list = ", ".join(sorted(extensions))
                print(f"{package_name}: {ext_list}")
            else:
                print(f"{package_name}: (no extensions found)")

        print(f"\nTotal packages: {len(package_to_extensions)}")
        used_count = sum(1 for exts in package_to_extensions.values() if exts)
        print(f"Packages used by extensions: {used_count}")
        print(f"Packages not used by extensions: {len(package_to_extensions) - used_count}")

    def save_package_extensions_json(self, package_to_extensions: Dict[str, Set[str]], output_file: str) -> None:
        """Save package-to-extensions mapping to JSON file."""
        json_data = {pkg: sorted(list(exts)) for pkg, exts in package_to_extensions.items()}
        output_data = {
            "package_to_extensions": json_data,
            "summary": {
                "total_packages": len(package_to_extensions),
                "packages_with_extensions": sum(1 for exts in package_to_extensions.values() if exts),
                "packages_without_extensions": sum(1 for exts in package_to_extensions.values() if not exts),
            },
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Package-to-extensions mapping saved to {output_file}")

    def save_package_extensions_with_dependencies_json(
        self, package_info: Dict[str, Dict[str, Any]], output_file: str
    ) -> None:
        """Save package-to-extensions mapping with dependency information to JSON file."""
        json_data = {}
        for pkg, info in package_info.items():
            json_data[pkg] = {
                "extensions": sorted(list(info["extensions"])),
                "dependency_of": sorted(list(info["dependency_of"])),
            }

        direct_usage = sum(1 for info in package_info.values() if info["extensions"])
        transitive_deps = sum(1 for info in package_info.values() if not info["extensions"] and info["dependency_of"])
        unused = sum(1 for info in package_info.values() if not info["extensions"] and not info["dependency_of"])

        output_data = {
            "package_info": json_data,
            "summary": {
                "total_packages": len(package_info),
                "directly_used": direct_usage,
                "transitive_dependencies": transitive_deps,
                "potentially_unused": unused,
            },
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Package information with dependencies saved to {output_file}")
        print(f"  Directly used: {direct_usage}")
        print(f"  Transitive dependencies: {transitive_deps}")
        print(f"  Potentially unused: {unused}")

    def print_results(
        self, results: Dict[str, Dict[str, List]], all_imports: Set[str], show_imports: bool = False
    ) -> None:
        """Print validation results to console."""
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

            if used_packages and len(used_packages) <= 10:
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
    ) -> None:
        """Save results to a JSON file."""
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


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze pip*.toml usage, validate dependencies, and update SWIPAT usage comments"
    )
    parser.add_argument("--root", type=str, default=".", help="Root directory of the repository (default: current)")
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=["_build/linux-x86_64/release", "source", "exts"],
        help="Directories to search for Python files",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--show-imports", action="store_true", help="Show all imports found in the codebase")
    parser.add_argument("--output-json", type=str, help="Write validation results to a JSON file")
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
    parser.add_argument(
        "--package-extensions",
        action="store_true",
        help="Analyze which extensions use which packages (for annotating pip.toml)",
    )
    parser.add_argument(
        "--package-extensions-json",
        type=str,
        help="Save package-to-extensions mapping to JSON file",
    )
    parser.add_argument(
        "--include-transitive-deps",
        action="store_true",
        help="Include transitive dependency information (requires pipdeptree)",
    )
    parser.add_argument(
        "--update-pip-toml",
        action="store_true",
        help="Update deps/pip*.toml files using computed package usage info",
    )
    parser.add_argument(
        "--package-info-json",
        type=str,
        default="package_extensions_with_deps.json",
        help="JSON file to load package usage info from when not analyzing",
    )
    return parser


def main() -> int:
    """Main entry point for the combined pip dependency tool."""
    parser = build_parser()
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    if not root_path.exists():
        print(f"Error: Root directory does not exist: {root_path}")
        return 1

    print(f"Working directory: {root_path}")
    print(f"Searching for Python files in: {', '.join(args.search_dirs)}")

    if not args.no_default_exclusions:
        print("Excluding test files by default (use --no-default-exclusions to include)")
    if args.exclude:
        print(f"Additional exclusions: {', '.join(args.exclude)}")

    exclusion_patterns = None
    if args.exclude:
        exclusion_patterns = (exclusion_patterns or []) + args.exclude

    use_pipdeptree = not args.no_pipdeptree

    if args.update_pip_toml and not (
        args.package_extensions or args.package_extensions_json or args.include_transitive_deps
    ):
        json_file = root_path / args.package_info_json
        if not json_file.exists():
            print(f"Error: package info JSON not found: {json_file}")
            return 1
        print(f"Loading package information from {json_file}")
        package_info = load_package_info(str(json_file))
        deps_dir = root_path / "deps"
        update_pip_toml_files(deps_dir, package_info)
        return 0

    validator = PipDependencyValidator(
        str(root_path),
        verbose=args.verbose,
        use_pipdeptree=use_pipdeptree,
        python_path=args.python_path,
        exclusion_patterns=exclusion_patterns,
    )

    if args.package_extensions or args.package_extensions_json or args.update_pip_toml:
        if args.include_transitive_deps or args.update_pip_toml:
            package_info = validator.analyze_package_extensions_with_dependencies(args.search_dirs)

            print("\n=== Package to Extensions Mapping (with Dependencies) ===\n")
            for package_name in sorted(package_info.keys()):
                info = package_info[package_name]
                if info["extensions"]:
                    ext_list = ", ".join(sorted(info["extensions"]))
                    print(f"{package_name}: {ext_list}")
                elif info["dependency_of"]:
                    dep_list = ", ".join(sorted(info["dependency_of"]))
                    print(f"{package_name}: (dependency of {dep_list})")
                else:
                    print(f"{package_name}: (no extensions found)")

            if args.package_extensions_json:
                validator.save_package_extensions_with_dependencies_json(package_info, args.package_extensions_json)

            if args.update_pip_toml:
                deps_dir = root_path / "deps"
                update_pip_toml_files(deps_dir, package_info)
        else:
            package_to_extensions = validator.analyze_package_extensions(args.search_dirs)
            validator.print_package_extensions(package_to_extensions)

            if args.package_extensions_json:
                validator.save_package_extensions_json(package_to_extensions, args.package_extensions_json)

            if args.update_pip_toml:
                package_info = {
                    pkg: {"extensions": exts, "dependency_of": set()} for pkg, exts in package_to_extensions.items()
                }
                deps_dir = root_path / "deps"
                update_pip_toml_files(deps_dir, package_info)
    else:
        results, all_imports, import_to_file = validator.validate_dependencies(args.search_dirs)
        validator.print_results(results, all_imports, show_imports=args.show_imports)

        if args.output_json:
            validator.save_results_json(results, all_imports, import_to_file, args.output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
