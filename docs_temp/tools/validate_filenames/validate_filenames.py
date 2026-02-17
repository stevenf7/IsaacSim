import argparse
import os
import re
import subprocess
import sys

# List of valid image and video file extensions
VALID_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".svg",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".flv",
    ".wmv",
    ".webm",
    ".webp",
}

# Define the detailed naming convention as a separate string
NAMING_CONVENTION = """
    isim_<VERSION_NUM>_<APP_TYPE>_<DOC_TYPE>_<APP_VIEW>_<YOUR_FILE_NAME>.filetype

    - VERSION_NUM: Should be x.y or x.y.z format (e.g., 4.5 or 2023.1.0).
    - APP_TYPE: Can be one of ros, replicator, isaaclab, full, base.
    - DOC_TYPE: Can be tut, ref, or ext-[extension_name]-[version] (e.g., ext-some_extension-1.2.3).
    - APP_VIEW: Can be one of gui, viewport, external.
    - YOUR_FILE_NAME: A non-empty string.
    - FILETYPE: A valid file extension (e.g., png, jpg, mp4).
"""

# ANSI color codes
RED = "\033[91m"  # Red for invalid sections
RESET = "\033[0m"  # Reset color to normal


# Function to print error messages for specific parts and filename details
def print_error(value, category, expected_format, file_path, details=None, print_valid=False):
    if print_valid:
        return  # Skip printing errors if --print-valid flag is enabled

    # Strip "(Invalid)" from the value when printing the error message
    value_without_invalid = value.replace(" (Invalid)", "")

    # Print error message for incorrect value without "(Invalid)"
    print(f"\nFile: {file_path}")
    print(f'{RED}"{value_without_invalid}" is an incorrect value for {category}.{RESET}')
    print(f"Expected format: {expected_format}")

    # Always print all available details up to this point
    if details:
        print("Details:")
        for key, val in details.items():
            # Highlight invalid sections in red in the details
            if "(Invalid)" in val:
                print(f"  {key}: {RED}{val}{RESET}")
                break  # Stop after printing first invalid detail
            else:
                print(f"  {key}: {val}")


# Function to print details for valid filenames
def print_valid_details_func(file_path, details):
    print(f"\nValid filename: {file_path}")
    print("Details:")
    for key, val in details.items():
        print(f"  {key}: {val}")
    print()


# Function to validate DOC_TYPE (specifically for extensions or other valid types)
def validate_extension(doc_type, file_path, details, print_valid):
    # Check if the DOC_TYPE starts with 'ext-' (for extensions)
    if doc_type.startswith("ext-"):
        ext_name_and_version = doc_type[4:]

        parts = ext_name_and_version.split("-")

        # Ensure there are at least two parts (name and version)
        if len(parts) < 2:
            details["DOC_TYPE"] = f"{doc_type} (Invalid)"
            print_error(
                doc_type,
                "DOC_TYPE",
                "'ext-[extension_name]-[version]' (e.g., ext-some_extension-1.2.3)",
                file_path,
                details,
            )
            return False

        ext_version = parts[-1]  # Last part is version
        ext_name = "-".join(parts[:-1])  # Join all parts except last one as extension name

        # Check that version follows x.y.z format
        if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", ext_version):
            details["DOC_TYPE"] = f"ext-{ext_name}-{ext_version} (Invalid)"
            print_error(
                f"ext-{ext_name}-{ext_version}",
                "DOC_TYPE (extension)",
                "'ext-[extension_name]-[version]' (e.g., ext-some_extension-1.2.3)",
                file_path,
                details,
            )
            return False

        # Validate that extension name contains valid characters
        if not re.match(r"^[a-zA-Z0-9\._]+$", ext_name):
            details["DOC_TYPE"] = f"ext-{ext_name} (Invalid)"
            print_error(
                f"ext-{ext_name}",
                "DOC_TYPE (extension)",
                "'ext-[extension_name]-[version]' (e.g., ext-some_extension-1.2.3)",
                file_path,
                details,
            )
            return False

        return True

    # Handle 'tut' and 'ref' as valid DOC_TYPEs
    elif doc_type in ["tut", "ref"]:
        details["DOC_TYPE"] = doc_type  # No need to mark invalid
        return True

    # If it's an unknown DOC_TYPE, mark it as invalid
    else:
        details["DOC_TYPE"] = f"{doc_type} (Invalid)"
        print_error(doc_type, "DOC_TYPE", "'tut', 'ref', or 'ext-[extension_name]-[version]'", file_path, details)
        return False


# Function to validate a filename based on the asset naming convention
def validate_filename(file_path, should_print_valid_details=False, print_valid=False):
    filename = os.path.basename(file_path)

    # Regular expression for validating the asset name (excluding DOC_TYPE validation)
    regex = r"^isim_([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+)_(ros|replicator|isaaclab|full|base)_(.+)_(gui|viewport|external)_(.+)\.([a-zA-Z0-9]+)$"
    match = re.match(regex, filename)

    # Initialize an empty dictionary for details
    details = {}

    if match:
        # Extract components into a dictionary
        details = {
            "VERSION_NUM": match.group(1),
            "APP_TYPE": match.group(2),
            "DOC_TYPE": match.group(3),
            "APP_VIEW": match.group(4),
            "YOUR_FILE_NAME": match.group(5),
            "FILETYPE": match.group(6),
        }

        # Validate DOC_TYPE (for extensions or other valid types)
        if not validate_extension(details["DOC_TYPE"], file_path, details, print_valid):
            return False

        # Validate APP_TYPE
        if details["APP_TYPE"] not in ["ros", "replicator", "isaaclab", "full", "base"]:
            details["APP_TYPE"] = f"{details['APP_TYPE']} (Invalid)"
            print_error(
                details["APP_TYPE"],
                "APP_TYPE",
                "'ros', 'replicator', 'isaaclab', 'full', or 'base'",
                file_path,
                details,
            )
            return False

        # Validate VERSION_NUM
        if not re.match(r"^[0-9]+\.[0-9]+(\.[0-9]+)?$", details["VERSION_NUM"]):
            details["VERSION_NUM"] = f"{details['VERSION_NUM']} (Invalid)"
            print_error(
                details["VERSION_NUM"], "VERSION_NUM", "'x.y' or 'x.y.z' (e.g., 4.5 or 2023.1.0)", file_path, details
            )
            return False

        # If the filename is valid and --print-valid flag is enabled, print the valid file path
        if print_valid:
            print(f"\nValid filename: {file_path}")

        # If the filename is valid and --print-valid-details is enabled, print details
        if should_print_valid_details:
            print_valid_details_func(file_path, details)

        return True

    else:
        # Manually extract parts of the filename for partial detail printing
        parts = filename.split("_")

        # Try to extract VERSION_NUM (first part after 'isim_')
        if len(parts) > 1 and re.match(r"^[0-9]+\.[0-9]+(\.[0-9]+)?$", parts[1]):
            details["VERSION_NUM"] = parts[1]
        else:
            details["VERSION_NUM"] = f"{parts[1]} (Invalid)" if len(parts) > 1 else "(Missing)"
            print_error(
                details["VERSION_NUM"], "VERSION_NUM", "'x.y' or 'x.y.z' (e.g., 4.5 or 2023.1.0)", file_path, details
            )
            return False  # Stop after printing error

        # Try to extract APP_TYPE (second part after VERSION_NUM)
        if len(parts) > 2:
            app_type_candidate = parts[2]
            if app_type_candidate not in ["ros", "replicator", "isaaclab", "full", "base"]:
                details["APP_TYPE"] = f"{app_type_candidate} (Invalid)"
                print_error(
                    details["APP_TYPE"],
                    "APP_TYPE",
                    "'ros', 'replicator', 'isaaclab', 'full', or 'base'",
                    file_path,
                    details,
                )
                return False  # Stop after printing error
            else:
                details["APP_TYPE"] = app_type_candidate

        # Try to extract DOC_TYPE (third part after APP_TYPE)
        if len(parts) > 3:
            doc_type_candidate = parts[3]
            if not validate_extension(doc_type_candidate, file_path, details, print_valid):
                return False  # Stop after printing error

        # Try to extract APP_VIEW (fourth part after DOC_TYPE)
        if len(parts) > 4:
            app_view_candidate = parts[4]
            if app_view_candidate not in ["gui", "viewport", "external"]:
                details["APP_VIEW"] = f"{app_view_candidate} (Invalid)"
                print_error(details["APP_VIEW"], "APP_VIEW", "'gui', 'viewport', or 'external'", file_path, details)
                return False  # Stop after printing error
            else:
                details["APP_VIEW"] = app_view_candidate

        # Try to extract YOUR_FILE_NAME (fifth part after APP_VIEW)
        if len(parts) > 5:
            details["YOUR_FILE_NAME"] = parts[5]

        # Print error with partial details
        print_error(
            filename,
            "filename",
            "Expected format: isim_<VERSION_NUM>_<APP_TYPE>_<DOC_TYPE>_<APP_VIEW>_<YOUR_FILE_NAME>.filetype",
            file_path,
            details,
        )

        return False


# Function to get the root directory of the Git repository
def get_git_root():
    try:
        git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return git_root
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None


def get_latest_commit_on_branch(branch):
    """Get the latest commit hash on a given branch."""
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", f"{branch}"], text=True).strip()
        return commit_hash
    except subprocess.CalledProcessError as e:
        print(f"Error getting latest commit for {branch}: {e}")
        return None


# Function to get the list of added, modified, and renamed files between current branch and main
def get_git_modified_or_added_files():
    try:
        git_root = get_git_root()
        if not git_root:
            return set()

        # Get the latest commit on the current branch (HEAD)
        current_commit = get_latest_commit_on_branch("HEAD")
        if not current_commit:
            return set()

        # Get the latest commit on the main branch
        main_commit = get_latest_commit_on_branch("main")
        if not main_commit:
            return set()

        # Get the list of modified, added, and renamed files between the current branch and the main branch
        modified_files = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", main_commit, current_commit], text=True, cwd=git_root
        ).splitlines()

        # Get untracked (new) files that are not yet staged
        untracked_files = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"], text=True, cwd=git_root
        ).splitlines()

        # Combine all lists of files and return their absolute paths
        return {os.path.join(git_root, file) for file in set(modified_files + untracked_files)}

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return set()


# Function to check if a file has a valid image or video extension
def is_valid_image_or_video_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in VALID_EXTENSIONS


# Function to validate files in the provided directory
def validate_files_in_directory(directory, should_print_valid_details=False, print_valid=False):
    # Expand tilde (~) to full home directory path
    directory = os.path.expanduser(directory)

    if not os.path.isdir(directory):
        print(f'Error: The directory "{directory}" does not exist.')
        return 0, 0

    total_files = 0
    errors_found = 0
    valid_files = 0  # Track valid files

    # Loop through the files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            # Only validate image or video files
            if is_valid_image_or_video_file(full_path):
                total_files += 1
                if validate_filename(full_path, should_print_valid_details, print_valid):
                    valid_files += 1
                else:
                    errors_found += 1

    return total_files, errors_found, valid_files


# Function to validate files in the provided list
def validate_files_in_list(file_list, should_print_valid_details=False, print_valid=False):

    total_files = 0
    errors_found = 0
    valid_files = 0

    # Loop through the files in the list
    for filepath in file_list:
        if is_valid_image_or_video_file(filepath):
            total_files += 1
            if validate_filename(filepath, should_print_valid_details, print_valid):
                valid_files += 1
            else:
                errors_found += 1

    return total_files, errors_found, valid_files


# Main function to handle command-line arguments and validate files
def main():
    # Combine the initial description with the naming convention
    parser_description = (
        """
    Validate filenames in a directory or Git branch based on a naming convention.

    The naming convention is expected to follow:
    """
        + NAMING_CONVENTION
    )

    # Use the combined description in argparse
    parser = argparse.ArgumentParser(description=parser_description, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        "--files", help="A list of filepaths separated by spaces (e.g., --files 'filename.jpg filename2.png')."
    )
    parser.add_argument(
        "--file-directory",
        help="The directory where the files will be searched and validated (e.g., --file-directory=/path/to/directory).",
    )
    parser.add_argument(
        "--print-valid-details", action="store_true", help="Print detailed information for valid files."
    )
    parser.add_argument("--print-valid", action="store_true", help="Displays valid filepaths.")

    args = parser.parse_args()

    total_files = 0
    errors_found = 0
    valid_files = 0
    git_diff_mode = False  # Flag to check if we're running in Git diff mode

    if args.files:
        # If --files argument is provided, validate files in the provided list
        file_list = args.files.split(" ")

        total_files, errors_found, valid_files = validate_files_in_list(
            file_list, args.print_valid_details, args.print_valid
        )

    elif args.file_directory:
        # If --file-directory argument is provided, validate files in the specified directory
        total_files, errors_found, valid_files = validate_files_in_directory(
            args.file_directory, args.print_valid_details, args.print_valid
        )
    else:
        # Otherwise, get the list of files that have been added or modified in the Git repository
        git_diff_mode = True  # We're running in Git diff mode
        files_to_check = get_git_modified_or_added_files()

        if not files_to_check:
            print("No added or modified files found in the Git repository!")
            print("For more options use --help")
            return

        total_files = 0
        errors_found = 0
        valid_files = 0

        # Validate each file from the Git diff
        for file in files_to_check:
            if os.path.isfile(file) and is_valid_image_or_video_file(file):
                total_files += 1
                if validate_filename(file, args.print_valid_details, args.print_valid):
                    valid_files += 1
                else:
                    errors_found += 1

    # Print summary
    if git_diff_mode:
        print(f"\nFound and checked {total_files} modified/added files.")
    else:
        print(f"\nTotal files checked: {total_files}")

    print(f"Valid files: {valid_files}")
    print("\nFor more options use --help")

    if errors_found > 0:
        print(f"Files with errors: {errors_found}")
        print("\nAll asset files should follow the convention:")
        print(NAMING_CONVENTION)
        sys.exit(1)


if __name__ == "__main__":
    main()
