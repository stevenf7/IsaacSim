# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
#!/usr/bin/env python3
"""
JUnit XML Test Report Generator

This script converts test results from a text file to a JUnit XML format for test reporting and CI integration.
It parses the repo_test_results.txt file and generates a standardized JUnit XML report that can be used
by continuous integration systems like Jenkins, GitLab CI, or GitHub Actions to display test results.

The JUnit XML format is widely supported by CI tools and provides a structured way to represent:
- Test suites and test cases
- Pass/fail/error/skip status
- Execution time
- Error messages and stack traces

Usage:
    python standalone_report.py <report_folder_path> <suite_name>
"""

import argparse
import os
import platform
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Tuple


class TestCase(NamedTuple):
    """Class representing a test case with its name and execution time."""

    name: str
    status: str
    execution_time: float


class Stats:
    """
    A class to store and manage test statistics for JUnit XML reporting.

    Attributes:
        passed (int): Number of passed tests
        failure (int): Number of failed tests
        error (int): Number of errors encountered
        skipped (int): Number of skipped tests
        total_time (float): Total execution time in seconds
    """

    def __init__(self):
        """Initialize the test statistics with default values."""
        self.passed = 0
        self.failure = 0
        self.error = 0
        self.skipped = 0
        self.total_time = 0.0

    def get_total(self) -> int:
        """
        Calculate the total number of tests.

        Returns:
            int: The sum of passed, failed, error, and skipped tests
        """
        return self.passed + self.failure + self.error + self.skipped


def parse_test_results(report_folder: str, suite_name: str) -> Tuple[ET.Element, List[TestCase]]:
    """
    Parse test results from report file and generate JUnit XML structure.

    This function reads the test results file and constructs a hierarchical XML structure
    conforming to the JUnit XML format, with test suites containing test cases and their
    associated metadata (status, execution time, error messages).

    Args:
        report_folder (str): Path to the folder containing test results
        suite_name (str): Name of the test suite for the JUnit XML report

    Returns:
        Tuple[ET.Element, List[TestCase]]: XML root element containing the complete JUnit test report structure
                                           and a list of TestCase objects for summary reporting
    """
    testsuites = ET.Element("testsuites")
    testcases = []
    errors = []
    stats = Stats()

    # List to store test case information for summary
    test_case_list = []

    results_file_path = os.path.join(report_folder, "repo_test_results.txt")

    # Regex patterns for parsing
    test_result_pattern = r"\[(retryok|ok|flaky|fail)\]\[(.*)s\](\[.*\])?(.*)"
    total_time_pattern = r"total time:\s(.*)s"

    with open(results_file_path) as result_file:
        lines = result_file.readlines()

        for line in lines:
            line = line.strip()

            # Parse test case results
            if any(status in line for status in ["[   ok   ]", "[retry ok]", "[  fail  ]", "[ flaky ]"]):
                clean_line = line.replace(" ", "")
                clean_line = clean_line.split("(Count:")[0]
                match = re.search(test_result_pattern, clean_line)

                if not match:
                    continue

                status, time_str, _, test_name = match.groups()
                if not test_name:
                    # Use the third group if fourth is empty (depends on regex match)
                    test_name = _

                # Parse test case name components
                test_parts = test_name.split("-")
                if len(test_parts) >= 3:
                    suite, classname = test_parts[1], test_parts[2]
                elif len(test_parts) > 1:
                    suite, classname = "pythontests", test_parts[1]
                else:
                    suite, classname = test_parts[0], test_parts[0]

                # Store execution time
                execution_time = float(time_str)

                # Create test case element
                testcase = ET.Element("testcase", name=suite, classname=classname, time=f"{execution_time:.3f}")

                # Store test case info for summary
                full_test_name = f"{suite}.{classname}"
                test_case_list.append(TestCase(full_test_name, status, execution_time))

                # Record test status
                if status == "fail":
                    stats.failure += 1
                    failure = ET.SubElement(testcase, "failure")
                    failure.text = f"{test_name} failed"
                else:
                    stats.passed += 1

                testcases.append(testcase)

            # Extract total execution time
            elif "total time" in line:
                match = re.search(total_time_pattern, line)
                if match:
                    stats.total_time = float(match.group(1))

            # Record error information
            elif "[ERROR]" in line:
                if stats.error == 0 and len(line.split()) > 1:
                    try:
                        stats.error = int(line.split()[1])
                    except (ValueError, IndexError):
                        # Handle case where error count is not a valid integer
                        pass
                errors.append(line)

        # Create testsuite element with statistics
        testsuite = ET.Element(
            "testsuite",
            name=suite_name,
            failures=str(stats.failure),
            errors=str(stats.error),
            skipped=str(stats.skipped),
            tests=str(stats.get_total()),
            time=f"{stats.total_time:.3f}",
            timestamp=datetime.now().isoformat(),
            hostname=platform.node(),
        )

        # Add error information if errors exist
        if errors:
            error_node = ET.SubElement(testsuite, "error")
            error_node.text = "".join(errors)

        testsuite.extend(testcases)
        testsuites.append(testsuite)

    return testsuites, test_case_list


def write_xml_report(testsuites: ET.Element, output_path: str) -> None:
    """
    Write the JUnit XML test report to a file.

    This function serializes the XML structure to a properly formatted JUnit XML file
    that can be consumed by CI systems and test reporting tools.

    Args:
        testsuites (ET.Element): XML structure containing the JUnit test report
        output_path (str): Path where the JUnit XML report will be written
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ET.tostring(testsuites, encoding="unicode", xml_declaration=True))


def print_test_summary(test_cases: List[TestCase]) -> None:
    """
    Print a summary of test cases sorted by execution time.

    Args:
        test_cases (List[TestCase]): List of test case information
    """
    if not test_cases:
        print("No test cases found to summarize.")
        return

    # Sort test cases by execution time (descending)
    sorted_tests = sorted(test_cases, key=lambda x: x.execution_time, reverse=True)

    # Calculate total execution time
    total_time = sum(test.execution_time for test in test_cases)

    # Print summary header
    print("\n" + "=" * 80)
    print(f"TEST EXECUTION SUMMARY (Total: {len(test_cases)} tests, {total_time:.2f} seconds)")
    print("=" * 80)
    print(f"{'TEST NAME':<60} {'STATUS':<10} {'TIME (s)':<10} {'% OF TOTAL':<10}")
    print("-" * 80)

    # Print each test case
    for test in sorted_tests:
        percentage = (test.execution_time / total_time) * 100 if total_time > 0 else 0
        status_display = "PASS" if test.status != "fail" else "FAIL"
        print(f"{test.name:<60} {status_display:<10} {test.execution_time:.3f}s{percentage:>9.1f}%")

    print("=" * 80)


def main(args: argparse.Namespace) -> None:
    """
    Main function to process test results and generate a JUnit XML report.

    This function coordinates the overall process of reading test results,
    generating the JUnit XML structure, and writing the final report file.
    A test execution summary sorted by execution time is printed at the end.

    Args:
        args (argparse.Namespace): Command line arguments
    """
    # Validate arguments
    if len(args.extra_args) < 2:
        print("Error: Missing required arguments")
        print("Usage: python standalone_report.py <report_folder_path> <suite_name>")
        return

    try:
        # Extract and validate arguments
        report_folder = os.path.abspath(args.extra_args[0])
        suite_name = args.extra_args[1]

        if not os.path.exists(report_folder):
            print(f"Error: Report folder '{report_folder}' does not exist")
            return

        results_file_path = os.path.join(report_folder, "repo_test_results.txt")
        if not os.path.exists(results_file_path):
            print(f"Error: Test results file not found at '{results_file_path}'")
            return

        # Process test results
        print(f"Processing report folder: {report_folder}")
        print(f"Suite name: {suite_name}")

        # Parse test results and generate XML structure
        testsuites, test_cases = parse_test_results(report_folder, suite_name)

        # Write XML report
        output_path = os.path.join(report_folder, "results.xml")
        print(f"Writing JUnit XML report to: {output_path}")
        write_xml_report(testsuites, output_path)

        # Always print test summary
        print_test_summary(test_cases)

        print("Report generation complete")

    except Exception as e:
        print(f"Error generating JUnit XML report: {str(e)}")
        import traceback

        traceback.print_exc()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert test results to JUnit XML format for CI reporting and test visualization"
    )
    parser.add_argument("extra_args", nargs="*", help="Additional arguments: <report_folder_path> <suite_name>")

    args = parser.parse_args()
    main(args)
