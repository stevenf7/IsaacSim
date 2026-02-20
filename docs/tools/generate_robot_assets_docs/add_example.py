#!/usr/bin/env python3
"""
Simple script to find robot names by their structural patterns in RST files.
This script looks for the pattern: "- Robot:" followed by the robot name
"""

import re


def find_robot_structure_lines(file_path):
    """
    Find the specific lines where robot structure patterns appear.
    Returns line numbers for lines containing "- Robot:" identifier.
    """
    structure_lines = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Look for robot identifier pattern: - Robot:
            if re.search(r"-\s*Robot:\s*", line):
                structure_lines.append(
                    {"line_number": line_num, "line_content": line.strip(), "type": "robot_identifier"}
                )

    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return []
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

    return structure_lines


def extract_robot_name_from_line(line):
    """
    Extract robot name from a line containing "- Robot:" identifier.
    """
    match = re.search(r"-\s*Robot:\s*([^\n]+)", line)
    if match:
        return match.group(1).strip()
    return None


def write_at_line(file_path, line_number, content):
    """
    Write content at a specific line in a file.

    Args:
        file_path: Path to the file
        line_number: Line number to write at (1-indexed)
        content: Content to write
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Insert new line at specified position
        lines.insert(line_number - 1, content + "\n")

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
            f.close()

        return True

    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return False
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False


def main():
    """Main function to demonstrate robot name finding."""

    # Example usage
    assets_doc = "docs/isaacsim/assets/usd_assets_robots.rst"
    examples_doc = "docs/isaacsim/introduction/menu_examples.rst"

    with open(examples_doc, "r", encoding="utf-8") as f:
        examples_content = f.read().split("\n")

    with open(assets_doc, "r", encoding="utf-8") as f:
        assets_content = f.readlines()

    print("\n2. Finding robot structure lines in file:")

    structure_lines = find_robot_structure_lines(assets_doc)

    if structure_lines:
        print(f"Found {len(structure_lines)} structure lines:")
        buffer = 0
        for line_info in structure_lines:

            # extract robot name from line
            robot_name = extract_robot_name_from_line(line_info["line_content"])
            line_place = len(assets_content)

            in_examples = False
            # check if robot name is in examples
            for example in examples_content:
                if robot_name in example:
                    in_examples = True
                    break

            # if robot is in examples, initialize line placement and header
            if in_examples:

                print(f"    Line {line_info['line_number']}: {example}")

                # find the exact place to put the header
                for i in range(line_info["line_number"], len(assets_content)):
                    if "- Robot:" in assets_content[i]:
                        line_place = i
                        break
                # write the header
                write_at_line(
                    assets_doc,
                    line_place + buffer - 7,
                    f"              * This robot appears in the following examples:",
                )
                buffer += 1

            if robot_name:
                for example in examples_content:
                    if robot_name in example:

                        write_at_line(
                            assets_doc, line_place + buffer - 7, f"                  {example.split('|')[0].strip()}"
                        )
                        buffer += 1

    else:
        print("No robot structure lines found.")


if __name__ == "__main__":
    main()
