import datetime
import os
import re

import tomlkit  # Install with 'pip install tomlkit'


def update_version_and_changelog(verbose=True):
    """
    Traverses the current working directory, locates the "config" and "docs" subdirectories,
    updates the version in "extension.toml" within "config" (under the "package" table),
    reads the latest version from "CHANGELOG.md" within "docs",
    adds a new changelog entry with the updated version below the "# Changelog" line,
    and writes the changes back to the files.

    Args:
      verbose: Whether to print verbose logging messages.
    """
    root_folder = os.getcwd()

    for dirpath, dirnames, filenames in os.walk(root_folder):
        if "config" in dirnames and "docs" in dirnames:
            config_path = os.path.join(dirpath, "config")
            toml_path = os.path.join(config_path, "extension.toml")
            docs_path = os.path.join(dirpath, "docs")
            changelog_path = os.path.join(docs_path, "CHANGELOG.md")

            if verbose:
                print(f"Processing directory: {dirpath}")

            try:
                # Update version in "extension.toml"
                if verbose:
                    print(f"  - Attempting to update version in: {toml_path}")

                with open(toml_path, "r") as f:
                    data = tomlkit.load(f)

                if "package" in data and "version" in data["package"]:
                    try:
                        major, minor, patch = map(int, str(data["package"]["version"]).split("."))
                        patch += 1
                        new_version = f"{major}.{minor}.{patch}"
                        data["package"]["version"] = new_version

                        with open(toml_path, "w") as f:
                            tomlkit.dump(data, f)

                        if verbose:
                            print(f"  - Updated {major}, {minor}, {patch} to {new_version} in: {toml_path}")

                    except ValueError:
                        print(f"  - Invalid version format found in {toml_path}")
                else:
                    print(f"  - 'package.version' key not found in: {toml_path}")

                # Update "CHANGELOG.md"
                if verbose:
                    print(f"  - Attempting to update changelog in: {changelog_path}")

                if os.path.exists(changelog_path):
                    with open(changelog_path, "r") as f:
                        lines = f.readlines()

                    changelog_line_index = None
                    for i, line in enumerate(lines):
                        if "# Changelog" in line:
                            changelog_line_index = i
                            break

                    if changelog_line_index is not None:
                        # Add new changelog entry after the "# Changelog" line
                        today = datetime.date.today().strftime("%Y-%m-%d")
                        new_entry = f"\n## [{new_version}] - {today}\n### Changed\n- Update extension description and add extension specific test settings\n\n"
                        lines.insert(changelog_line_index + 1, new_entry)

                        with open(changelog_path, "w") as f:
                            f.writelines(lines)

                        if verbose:
                            print(f"  - Added changelog entry for {new_version} in: {changelog_path}")
                    else:
                        print(f"  - '# Changelog' line not found in {changelog_path}")

                else:
                    print(f"  - 'CHANGELOG.md' not found in: {docs_path}")

            except Exception as e:
                print(f"Error processing files in {dirpath}: {e}")


if __name__ == "__main__":
    update_version_and_changelog(verbose=True)
