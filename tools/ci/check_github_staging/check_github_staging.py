import json
import mimetypes
import os
import sys


def is_text_file(filepath):
    """Detect if a file is text (for banned-word scanning) without relying on the 'file' command."""
    # Known text types by extension
    guessed_type, _ = mimetypes.guess_type(filepath)
    if guessed_type and guessed_type.startswith("text/"):
        return True
    # Common text extensions not always in mimetypes
    text_extensions = {
        ".py", ".pyi", ".pyx", ".sh", ".bash", ".bat", ".cmd",
        ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".cs", ".java",
        ".rs", ".go", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
        ".xml", ".html", ".htm", ".xhtml", ".css", ".scss", ".less",
        ".md", ".rst", ".txt", ".log", ".cmake", ".make", ".mk",
        ".rb", ".pl", ".pm", ".php", ".lua", ".r", ".sql",
        ".glsl", ".vert", ".frag", ".comp", ".hlsl",
        ".proto", ".thrift", ".graphql", ".gql", ".env",
        ".usd", ".usda", ".usdc",
    }
    ext = os.path.splitext(filepath)[1].lower()
    if ext in text_extensions:
        return True
    # For unknown extensions, sample content: treat as text if decodable and not binary
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
        if not chunk:
            return True
        # Reject if too many null bytes (binary)
        if chunk.count(b"\x00") > len(chunk) // 100:
            return False
        # Must be valid UTF-8 and mostly printable/newline/tab
        text = chunk.decode("utf-8")
        printable = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
        return printable >= len(text) * 0.85
    except (OSError, UnicodeDecodeError):
        return False


def check_path_for_banned_words(path: str):
    with open("./tools/ci/check_github_staging/banned_words.json", "r") as f:
        BANNED_WORDS = json.load(f)

    # Initialize results structures
    results_by_word = {word: {} for word in BANNED_WORDS["banned_words"]}
    results_by_file = {}
    allowed_patterns = BANNED_WORDS.get("allowed_patterns", [])

    # os.walk (not glob) so that dotfiles and dot-directories such as
    # .cursor/, .github/, and .gitignore are scanned too. Python's glob skips
    # hidden paths by default, which previously hid banned words living there.
    for root, dirs, files in os.walk(path):
        # The .git directory is metadata, not shipped content.
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            file = os.path.join(root, name)
            if os.path.isfile(file) and is_text_file(file):
                file_path = os.path.relpath(file, path).replace(os.sep, "/")
                if file_path not in BANNED_WORDS["whitelisted_files"]:
                    try:
                        f = open(file, "r", errors="replace")
                    except OSError:
                        continue
                    with f:
                        for line_num, line in enumerate(f, 1):
                            for banned_word in BANNED_WORDS["banned_words"]:
                                if banned_word in line and not any(ap in line for ap in allowed_patterns):
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
