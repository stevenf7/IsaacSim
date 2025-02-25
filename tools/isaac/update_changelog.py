import argparse  # Added import
import datetime
import os
import re
import subprocess

import tomlkit  # Install with 'pip install tomlkit'


def update_version_and_changelog(
    root_folder=None, verbose=True, check_cpp=False, check_modified=False, changelog_message=None
):
    """
    Traverses directories and updates extension versions/changelogs based on criteria.
    """
    root_folder = root_folder or os.getcwd()

    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Prune non-extension directories early
        if "config" not in dirnames or "docs" not in dirnames:
            continue

        dirnames[:] = []  # Prevent descending into subdirectories
        extension_name = os.path.basename(dirpath)

        if verbose:
            print(f"\n📦 Processing extension: {extension_name}")

        try:
            # Pre-check conditions
            if not should_process_extension(dirpath, check_cpp, check_modified, verbose):
                continue

            # Path validation
            config_path = os.path.join(dirpath, "config")
            docs_path = os.path.join(dirpath, "docs")
            toml_path = os.path.join(config_path, "extension.toml")
            changelog_path = os.path.join(docs_path, "CHANGELOG.md")

            if not validate_paths(toml_path, changelog_path, verbose):
                continue

            # Core processing
            new_version = update_extension_version(toml_path, verbose)
            if new_version:
                update_changelog_file(changelog_path, new_version, verbose, changelog_message)

        except Exception as e:
            handle_processing_error(dirpath, e, verbose)


# New helper functions
def should_process_extension(dirpath, check_cpp, check_modified, verbose):
    """Check all conditional requirements for processing"""
    if check_modified and not has_git_changes(dirpath, verbose):
        return False
    if check_cpp and not has_cpp_files(dirpath, verbose):
        return False
    return True


def has_git_changes(dirpath, verbose):
    """Check if directory has changes against develop branch"""
    try:
        result = subprocess.run(["git", "diff", "--quiet", "develop", "--", dirpath], capture_output=True, text=True)
        if result.returncode == 0:
            if verbose:
                print(f"  ⏭️  No uncommitted changes vs develop branch")
            return False
        return True
    except Exception as e:
        if verbose:
            print(f"  ❌ Git check failed: {str(e)}")
        return False


def has_cpp_files(dirpath, verbose):
    """Check for C++ source files in directory tree"""
    for root, _, files in os.walk(dirpath):
        for file in files:
            if file.endswith((".cpp", ".hpp", ".h", ".cxx")):
                return True
    if verbose:
        print(f"  ⏭️  No C++ files found in extension")
    return False


def validate_paths(toml_path, changelog_path, verbose):
    """Validate required files exist"""
    if not os.path.exists(toml_path):
        if verbose:
            print(f"  ❌ Missing extension.toml at {toml_path}")
        return False
    if not os.path.exists(changelog_path):
        if verbose:
            print(f"  ❌ Missing CHANGELOG.md at {changelog_path}")
        return False
    return True


def update_extension_version(toml_path, verbose):
    """Update version in extension.toml and return new version"""
    try:
        with open(toml_path, "r") as f:
            data = tomlkit.load(f)

        package = data.get("package", {})
        version_str = package.get("version", "")

        if not version_str:
            if verbose:
                print(f"  ❌ Missing 'package.version' in extension.toml")
            return None

        try:
            parts = list(map(int, version_str.split(".")))
            if len(parts) != 3:
                raise ValueError
        except ValueError:
            if verbose:
                print(f"  ❌ Invalid version format '{version_str}', expected X.Y.Z")
            return None

        parts[-1] += 1  # Increment patch version
        new_version = ".".join(map(str, parts))
        data["package"]["version"] = new_version

        with open(toml_path, "w") as f:
            tomlkit.dump(data, f)

        if verbose:
            print(f"  ✅ Version updated: {version_str} → {new_version}")
        return new_version

    except Exception as e:
        if verbose:
            print(f"  ❌ Failed to update version: {str(e)}")
        return None


def update_changelog_file(changelog_path, new_version, verbose, changelog_message=None):
    """Add new entry to changelog"""
    try:
        with open(changelog_path, "r") as f:
            content = f.read()

        changelog_header = "# Changelog"
        if changelog_header not in content:
            if verbose:
                print(f"  ❌ Changelog header not found")
            return

        today = datetime.date.today().strftime("%Y-%m-%d")
        default_message = "Update extension description and add extension specific test settings"
        message = changelog_message or default_message

        new_entry = f"\n## [{new_version}] - {today}\n" "### Changed\n" f"- {message}\n\n"

        updated_content = content.replace(changelog_header, f"{changelog_header}{new_entry}", 1)

        with open(changelog_path, "w") as f:
            f.write(updated_content)

        if verbose:
            print(f"  ✅ Changelog updated with version {new_version}")

    except Exception as e:
        if verbose:
            print(f"  ❌ Failed to update changelog: {str(e)}")


def handle_processing_error(dirpath, error, verbose):
    """Handle errors during processing"""
    if verbose:
        print(f"\n  🚨 Error processing {os.path.basename(dirpath)}")
        print(f"  🔍 Error details: {str(error)}")
    else:
        print(f"Error in {os.path.basename(dirpath)}: {str(error)}")


if __name__ == "__main__":
    # Replace original main with argument parsing
    parser = argparse.ArgumentParser(description="Update extension version and changelog.")
    parser.add_argument(
        "root", nargs="?", default=os.getcwd(), help="Root directory to process (default: current directory)"
    )
    parser.add_argument("--quiet", action="store_false", dest="verbose", help="Disable verbose output")
    parser.add_argument("--check-cpp", action="store_true", help="Only update extensions with C++ source files")
    parser.add_argument(
        "--check-modified", action="store_true", help="Only update extensions with changes vs develop branch"
    )
    parser.add_argument(
        "--message",
        "-m",
        help="Custom changelog message (default: Update extension description and add extension specific test settings)",
    )
    args = parser.parse_args()

    update_version_and_changelog(
        root_folder=args.root,
        verbose=args.verbose,
        check_cpp=args.check_cpp,
        check_modified=args.check_modified,
        changelog_message=args.message,
    )
