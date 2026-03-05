import glob
import json
import mimetypes
import os
import subprocess
import sys


def is_text_file(filepath):
    # Run the 'file' command and capture its output
    result = subprocess.run(["file", "--mime", filepath], capture_output=True, text=True)
    output = result.stdout
    # Check if the output contains 'text/'
    return "text/" in output


def check_path_for_banned_words(path: str):
    with open("./tools/ci/check_github_staging/banned_words.json", "r") as f:
        BANNED_WORDS = json.load(f)

    # Initialize results structures
    results_by_word = {word: {} for word in BANNED_WORDS["banned_words"]}
    results_by_file = {}

    for file in glob.glob(path + "**/**", recursive=True):
        if os.path.isfile(file) and is_text_file(file):
            file_path = file.removeprefix(path).removeprefix("/")
            if file_path not in BANNED_WORDS["whitelisted_files"]:
                with open(file, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        for banned_word in BANNED_WORDS["banned_words"]:
                            if banned_word in line:
                                # Add to word-based results with nested structure
                                if file_path not in results_by_word[banned_word]:
                                    results_by_word[banned_word][file_path] = []
                                results_by_word[banned_word][file_path].append(
                                    {"line_number": line_num, "line_content": line.strip()}
                                )

                                # Add to file-based results
                                if file_path not in results_by_file:
                                    results_by_file[file_path] = []
                                results_by_file[file_path].append(
                                    {"banned_word": banned_word, "line_number": line_num, "line_content": line.strip()}
                                )

    # Save both result formats
    with open("results.json", "w") as f:
        json.dump(results_by_word, f, indent=4)
    with open("results_by_file.json", "w") as f:
        json.dump(results_by_file, f, indent=4)

    return results_by_word, results_by_file


if __name__ == "__main__":
    _, results_by_file = check_path_for_banned_words(sys.argv[1])
    num_files = len(results_by_file)
    if num_files > 0:
        print(
            f"Banned word check failed: found banned words in {num_files} file(s). "
            "See results.json and results_by_file.json for details.",
            file=sys.stderr,
        )
    else:
        print("Banned word check passed: no banned words found.")
    sys.exit(num_files)
