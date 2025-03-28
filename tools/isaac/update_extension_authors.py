#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import toml


# Get repository root based on script location
def get_repo_root():
    """Get the repository root based on script location.
    The script is guaranteed to be in tools/isaac directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two directories (from tools/isaac to repo root)
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    return repo_root


# Default paths based on repository structure
REPO_ROOT = get_repo_root()
DEFAULT_EXTENSIONS_DIR = os.path.join(REPO_ROOT, "source", "extensions")
DEFAULT_REPO_ROOT = REPO_ROOT


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update extension.toml files with top contributors from git history")
    parser.add_argument(
        "--extensions-dir",
        default=DEFAULT_EXTENSIONS_DIR,
        help=f"Path to extensions directory (default: {DEFAULT_EXTENSIONS_DIR})",
    )
    parser.add_argument(
        "--repo-root", default=DEFAULT_REPO_ROOT, help=f"Path to git repository root (default: {DEFAULT_REPO_ROOT})"
    )
    parser.add_argument(
        "--max-contributors", type=int, default=3, help="Maximum number of top contributors to include (default: 3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only show what would be changed without actually modifying files"
    )
    parser.add_argument("--extension", help="Process only a specific extension directory (basename only)")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate a summary of extensions assigned to each author (based on current extension.toml files)",
    )
    parser.add_argument(
        "--summary-only", action="store_true", help="Only generate the author summary without updating files"
    )
    parser.add_argument("--missing-authors-only", action="store_true", help="Only show extensions missing authors")
    parser.add_argument(
        "--fix-missing-authors",
        action="store_true",
        help="Update only extensions that are missing authors based on git history",
    )
    parser.add_argument(
        "--update-codeowners", action="store_true", help="Update CODEOWNERS file with authors from each extension.toml"
    )
    parser.add_argument(
        "--codeowners-file",
        default="CODEOWNERS",
        help="Path to CODEOWNERS file, relative to repo root (default: CODEOWNERS)",
    )

    return parser.parse_args()


def get_top_contributors(extension_path, repo_root, max_contributors=3):
    """Get the top N contributors for a specific extension path."""
    try:
        # Get relative path from repo root to extension
        rel_path = os.path.relpath(extension_path, repo_root)

        # Use git log to get the commit history with author emails for this directory
        cmd = ["git", "-C", repo_root, "log", "--format=%ae", "--no-merges", "--", rel_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Count occurrences of each email
            emails = result.stdout.strip().split("\n")
            if not emails or emails[0] == "":
                print(f"No commit history found for {rel_path}")
                return []

            # Count and get top N contributors
            email_counter = Counter(emails)
            top_contributors = [email for email, _ in email_counter.most_common(max_contributors)]

            return top_contributors
        except subprocess.CalledProcessError:
            print(f"Git command failed for {rel_path}, falling back to current authors")
            # Fall back to current authors if git fails
            return get_current_authors(extension_path)
    except Exception as e:
        print(f"Error getting contributors for {extension_path}: {e}")
        return []


def get_current_authors(extension_path):
    """Read the current authors from the extension.toml file."""
    toml_path = os.path.join(extension_path, "config", "extension.toml")

    if not os.path.exists(toml_path):
        print(f"extension.toml not found at {toml_path}")
        return []

    try:
        # Read the TOML file content
        with open(toml_path, "r") as f:
            content = f.read()

        # Use regex to extract the authors list
        authors_match = re.search(r"authors\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if not authors_match:
            print(f"No authors field found in {toml_path}")
            return []

        # Extract author emails from the match
        authors_str = authors_match.group(1)
        # Use regex to find all quoted strings (author emails)
        authors = re.findall(r'"([^"]*)"', authors_str)

        return authors
    except Exception as e:
        print(f"Error reading authors from {toml_path}: {e}")
        return []


def update_extension_toml(extension_path, top_contributors, dry_run=False):
    """Update the extension.toml file with top contributors."""
    toml_path = os.path.join(extension_path, "config", "extension.toml")

    if not os.path.exists(toml_path):
        print(f"extension.toml not found at {toml_path}")
        return False

    try:
        # Read the TOML file content
        with open(toml_path, "r") as f:
            content = f.read()

        # If there are no contributors, keep the original authors
        if not top_contributors:
            print(f"No contributors found for {extension_path}, keeping original authors")
            return False

        # Format contributor list properly for TOML (with quotes around each email)
        formatted_contributors = "[" + ", ".join(f'"{email}"' for email in top_contributors) + "]"
        new_authors = f"authors = {formatted_contributors}"

        # Replace the authors field using regex to preserve formatting
        updated_content = re.sub(r"authors\s*=\s*\[[^\]]*\]", new_authors, content)

        # Check if replacement actually happened
        if updated_content == content:
            print(f"Warning: Could not find authors field in {toml_path}")
            return False

        # Write the updated content back (unless dry run)
        if not dry_run:
            with open(toml_path, "w") as f:
                f.write(updated_content)
            print(f"Updated authors in {toml_path} to {formatted_contributors}")
        else:
            print(f"Would update authors in {toml_path} to {formatted_contributors}")

        return True
    except Exception as e:
        print(f"Error updating {toml_path}: {e}")
        return False


def update_codeowners_file(repo_root, extension_contributors, codeowners_file="CODEOWNERS", dry_run=False):
    """Update the CODEOWNERS file with authors from each extension.toml."""
    codeowners_path = os.path.join(repo_root, codeowners_file)

    # Get repository name from the directory name
    repo_name = os.path.basename(repo_root)

    # Default header for new CODEOWNERS file if it doesn't exist
    default_header = f"""# CODEOWNERS for {repo_name} repository
# See https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

# These owners will be the default owners for everything in the repo
# Unless a later match takes precedence, they will be requested for
# review when someone opens a pull request.
* hmazhar@nvidia.com 

# Extension-specific code owners
# Generated from extension.toml author lists
"""

    try:
        # Check if CODEOWNERS file exists and read it
        if os.path.exists(codeowners_path):
            with open(codeowners_path, "r") as f:
                content = f.read()

            # Extract the header (everything before any extension-specific entries)
            header_match = re.search(r"(.*?)# Extension-specific code owners", content, re.DOTALL)
            if header_match:
                header = header_match.group(1)
                # Add the "Extension-specific code owners" line back
                header += "# Extension-specific code owners\n# Generated from extension.toml author lists\n"
            else:
                # If no extension-specific section exists, preserve everything as header
                # and add our extension-specific marker
                header = content
                if not header.endswith("\n\n"):
                    if header.endswith("\n"):
                        header += "\n"
                    else:
                        header += "\n\n"
                header += "# Extension-specific code owners\n# Generated from extension.toml author lists\n"
        else:
            # Use default header for new file
            header = default_header
            print(f"CODEOWNERS file not found at {codeowners_path}, will create a new one")

        # Generate extension-specific entries
        entries = []

        for ext_name, authors in extension_contributors.items():
            if not authors:
                print(f"Skipping {ext_name} in CODEOWNERS (no authors)")
                continue

            # Get the extension path relative to the repo root
            ext_path = f"source/extensions/{ext_name}/"

            # Format the author list (space-separated)
            formatted_authors = " ".join(authors)

            # Add entry
            entries.append(f"{ext_path} {formatted_authors}")

        # Sort entries for consistency
        entries.sort()

        # Combine header and entries
        new_content = header + "\n" + "\n".join(entries) + "\n"

        # Write the updated content back (unless dry run)
        if not dry_run:
            with open(codeowners_path, "w") as f:
                f.write(new_content)
            print(f"Updated CODEOWNERS file at {codeowners_path} with {len(entries)} extension entries")
        else:
            print(f"Would update CODEOWNERS file at {codeowners_path} with {len(entries)} extension entries")

        return True
    except Exception as e:
        print(f"Error updating CODEOWNERS file: {e}")
        return False


def check_extensions_dir(extensions_dir):
    """Verify the extensions directory exists."""
    if not os.path.isdir(extensions_dir):
        print(f"Error: Extensions directory not found at {extensions_dir}")
        return False
    return True


def generate_contributor_summary(extension_contributors, missing_authors_only=False):
    """Generate and print a summary of extensions per contributor."""
    # Count how many extensions each contributor appears in
    contributor_counts = Counter()
    extension_count = len(extension_contributors)

    # Track extensions without authors
    extensions_without_authors = []

    # Collect all contributors across all extensions
    for ext_name, contributors in extension_contributors.items():
        if not contributors:
            extensions_without_authors.append(ext_name)
            continue

        for contributor in contributors:
            contributor_counts[contributor] += 1

    # If only showing missing authors, skip the rest of the summary
    if missing_authors_only:
        if extensions_without_authors:
            print(f"\n===== EXTENSIONS MISSING AUTHORS =====")
            print(f"Found {len(extensions_without_authors)} extensions without authors:")
            for ext_name in sorted(extensions_without_authors):
                print(f"- {ext_name}")
        else:
            print("\nAll extensions have authors defined.")
        return

    # Sort contributors by number of extensions they contribute to (descending)
    sorted_contributors = sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True)

    # Print summary
    print("\n===== AUTHOR SUMMARY =====")
    print(f"Total Extensions: {extension_count}")
    print(f"Total Authors: {len(contributor_counts)}")

    # Print extensions without authors if any exist
    if extensions_without_authors:
        print(f"\n===== EXTENSIONS MISSING AUTHORS =====")
        print(f"Found {len(extensions_without_authors)} extensions without authors:")
        for ext_name in sorted(extensions_without_authors):
            print(f"- {ext_name}")

    print("\nAuthors by number of extensions:")

    # Print each contributor and how many extensions they're associated with
    for contributor, count in sorted_contributors:
        percentage = (count / extension_count) * 100
        print(f"{contributor}: {count} extensions ({percentage:.1f}%)")


def main():
    # Parse command line arguments
    args = parse_args()

    # Determine if we only need to run in summary mode
    summary_mode_only = args.summary_only or (args.summary and args.dry_run)
    codeowners_mode = args.update_codeowners
    fix_missing_mode = args.fix_missing_authors

    if fix_missing_mode:
        print("Starting missing author fix process...")
    elif codeowners_mode:
        print("Starting CODEOWNERS update process...")
    else:
        print(f"Starting extension author {'summary' if summary_mode_only else 'update'} process...")

    # Check if extensions directory exists
    if not check_extensions_dir(args.extensions_dir):
        return

    # Get extension directories to process
    if args.extension:
        # Process only a specific extension
        ext_path = os.path.join(args.extensions_dir, args.extension)
        if not os.path.isdir(ext_path):
            print(f"Error: Extension directory not found: {ext_path}")
            return
        extension_dirs = [ext_path]
    else:
        # Process all extensions
        try:
            extension_dirs = [
                os.path.join(args.extensions_dir, d)
                for d in os.listdir(args.extensions_dir)
                if os.path.isdir(os.path.join(args.extensions_dir, d))
            ]
        except FileNotFoundError:
            print(f"Error: Extensions directory not found at {args.extensions_dir}")
            return

    print(f"Found {len(extension_dirs)} extension directories to process")
    if args.dry_run:
        print("DRY RUN: No files will be modified")

    # Process each extension
    success_count = 0
    error_count = 0
    skipped_count = 0

    # Dictionary to store contributors for each extension for summary or CODEOWNERS update
    extension_contributors = {}

    for ext_dir in extension_dirs:
        ext_name = os.path.basename(ext_dir)
        print(f"\nProcessing {ext_name}...")

        # For summary mode or CODEOWNERS update, read current authors instead of git history
        if args.summary or args.summary_only or codeowners_mode:
            current_authors = get_current_authors(ext_dir)
            if current_authors:
                print(f"Current authors: {current_authors}")
                extension_contributors[ext_name] = current_authors
                success_count += 1
            else:
                extension_contributors[ext_name] = []  # Include extensions with empty author lists
                skipped_count += 1
                print(f"No authors found in extension.toml")
            continue

        # For fix-missing-authors mode, only update extensions with missing authors
        if fix_missing_mode:
            current_authors = get_current_authors(ext_dir)
            if current_authors:
                print(f"Skipping {ext_name} (already has authors: {current_authors})")
                extension_contributors[ext_name] = current_authors
                skipped_count += 1
                continue
            else:
                print(f"Will update missing authors for {ext_name}")

        # Get top contributors from git history for update mode
        top_contributors = get_top_contributors(ext_dir, args.repo_root, args.max_contributors)
        if top_contributors:
            # Store contributors for potential summary
            extension_contributors[ext_name] = top_contributors

            print(f"Top contributors: {top_contributors}")

            # Update extension.toml
            if update_extension_toml(ext_dir, top_contributors, args.dry_run):
                success_count += 1
            else:
                error_count += 1
        else:
            skipped_count += 1

    # Update CODEOWNERS file if requested
    if codeowners_mode:
        update_codeowners_file(args.repo_root, extension_contributors, args.codeowners_file, args.dry_run)

    # Print operation summary
    if not args.summary_only and not codeowners_mode:
        print(f"\nOperation Summary:")
        print(f"- Successfully updated: {success_count} extensions")
        print(f"- Failed to update: {error_count} extensions")
        print(f"- Skipped (no contributors or already has authors): {skipped_count} extensions")
        print(f"- Total processed: {len(extension_dirs)} extensions")

    # Generate and print contributor summary if requested
    if args.summary or args.summary_only:
        generate_contributor_summary(extension_contributors, args.missing_authors_only)


if __name__ == "__main__":
    main()
