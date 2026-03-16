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

Enhanced Error Reporting:
    This script can parse detailed error messages for failed tests from the full test output.
    The full output file should be named 'full_output.txt' in the report folder.

    When using test_isaac.py (recommended), the full output is automatically captured.
    This provides much richer failure information in the JUnit XML report, which will be
    displayed by GitLab and other CI systems.

    Manual usage (if not using test_isaac.py):

        ./repo.sh test -s benchmarks --generate-report 2>&1 | tee _build/linux-x86_64/release/_testoutput/full_output.txt
        ./repo.sh ci standalone_report -- _build/linux-x86_64/release/_testoutput benchmarks

Usage:
    python standalone_report.py <report_folder_path> <suite_name>
"""

import argparse
import os
import platform
import re
import shutil
import sys
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

# Debug mode: set to True to enable detailed logging
DEBUG_MODE = False


class Config:
    """Configuration constants and patterns for test report generation."""

    # Test status constants
    class Status:
        PASS = "ok"
        FAIL = "fail"
        FLAKY = "flaky"
        RETRY_OK = "retryok"

        @classmethod
        def get_all(cls) -> List[str]:
            """Get all valid test status values."""
            return [cls.PASS, cls.FAIL, cls.FLAKY, cls.RETRY_OK]

        @classmethod
        def get_display_map(cls) -> Dict[str, str]:
            """Get status to display name mapping."""
            return {cls.PASS: "PASS", cls.FAIL: "FAIL", cls.FLAKY: "FLAKY", cls.RETRY_OK: "RETRY_OK"}

    # File patterns
    RESULTS_FILENAME = "repo_test_results.txt"
    OUTPUT_FILENAME = "results.xml"
    FULL_OUTPUT_FILENAME = "full_output.txt"  # Optional file with detailed errors

    # Regex patterns
    class Patterns:
        # Status pattern mapping
        STATUS_PATTERNS = [
            (r"\[\s*ok\s*\]", "ok"),
            (r"\[\s*retry\s*ok\s*\]", "retryok"),
            (r"\[\s*fail\s*\]", "fail"),
            (r"\[\s*flaky\s*\]", "flaky"),
        ]

        # Test result extraction pattern
        TEST_RESULT = r"\[(?:retryok|ok|flaky|fail)\]\[([0-9.]+)s\](?:\[[^\]]*\])?(.*)"

        # Total time extraction pattern
        TOTAL_TIME = r"total\s+time:\s*([0-9.]+)s"

        # Error line pattern
        ERROR_LINE = r"\[ERROR\]"

        # Carb/kit log file path (from "[Info] [carb] Logging to file: <path>")
        # Prefer exact match; fallback matches "Logging to file:" for encoding-robustness (e.g. UTF-16 on Windows)
        CARB_LOGGING_LINE = r"\[Info\] \[carb\] Logging to file:\s*(.+)"
        CARB_LOGGING_LINE_RELAXED = re.compile(r"Logging to file:\s*(.+)", re.IGNORECASE)

        # Kit log block starter: line contains a level tag like ] [Info] or ] [Error] (multi-line blocks)
        KIT_LOG_LEVEL = re.compile(r"\]\s*\[(?:Info|Warning|Error|Critical)\]")

    # Display formatting
    class Display:
        SUMMARY_WIDTH = 90
        TEST_NAME_WIDTH = 60
        STATUS_WIDTH = 12
        TIME_WIDTH = 10
        PERCENT_WIDTH = 8


class TestCase(NamedTuple):
    """Class representing a test case with its name, status, and execution time."""

    name: str
    status: str
    execution_time: float
    error_message: Optional[str] = None


class TestStats:
    """
    A class to store and manage test statistics for JUnit XML reporting.

    Attributes:
        passed (int): Number of passed tests
        failure (int): Number of failed tests
        error (int): Number of errors encountered
        skipped (int): Number of skipped tests
        flaky (int): Number of flaky tests
        total_time (float): Total execution time in seconds
    """

    def __init__(self):
        """Initialize the test statistics with default values."""
        self.passed = 0
        self.failure = 0
        self.error = 0
        self.skipped = 0
        self.flaky = 0
        self.total_time = 0.0

    def get_total(self) -> int:
        """
        Calculate the total number of tests.

        Returns:
            int: The sum of passed, failed, error, skipped, and flaky tests
        """
        return self.passed + self.failure + self.error + self.skipped + self.flaky

    def update_for_status(self, status: str) -> None:
        """Update statistics based on test status."""
        if status == Config.Status.FAIL:
            self.failure += 1
        elif status == Config.Status.FLAKY:
            self.flaky += 1
        elif status in [Config.Status.PASS, Config.Status.RETRY_OK]:
            self.passed += 1
        else:
            ErrorHandler.warn(f"Unknown test status '{status}', counting as passed")
            self.passed += 1


class ErrorHandler:
    """Centralized error handling and logging."""

    @staticmethod
    def warn(message: str) -> None:
        """Print warning message."""
        print(f"Warning: {message}")

    @staticmethod
    def error(message: str) -> None:
        """Print error message."""
        print(f"Error: {message}")

    @staticmethod
    def fatal(message: str, exit_code: int = 1) -> None:
        """Print error message and exit."""
        print(f"Error: {message}")
        sys.exit(exit_code)

    @staticmethod
    def handle_exception(e: Exception, context: str) -> None:
        """Handle exception with context."""
        print(f"Error {context}: {str(e)}")
        import traceback

        traceback.print_exc()


class Validator:
    """Input validation utilities."""

    @staticmethod
    def validate_file_exists(file_path: Union[str, Path]) -> bool:
        """Validate that a file exists."""
        return Path(file_path).exists()

    @staticmethod
    def validate_directory_exists(dir_path: Union[str, Path]) -> bool:
        """Validate that a directory exists."""
        return Path(dir_path).is_dir()

    @staticmethod
    def validate_float(value: str, context: str = "") -> Optional[float]:
        """Validate and convert string to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            ErrorHandler.warn(f"Invalid float format '{value}'" + (f" in {context}" if context else ""))
            return None


class TestResultParser:
    """Parser for test result lines and files."""

    @staticmethod
    def parse_test_line(line: str) -> Optional[TestCase]:
        """
        Parse a single test result line and extract test information.

        Args:
            line (str): A single line from the test results file

        Returns:
            Optional[TestCase]: TestCase object if parsing successful, None otherwise
        """
        # Check if line contains test status indicators
        matched_status = None
        for pattern, status in Config.Patterns.STATUS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                matched_status = status
                break

        if not matched_status:
            return None

        # Clean the line for regex parsing
        clean_line = re.sub(r"\s+", "", line)  # Remove all whitespace
        clean_line = clean_line.split("(Count:")[0]  # Remove count information

        # Extract components using regex
        match = re.search(Config.Patterns.TEST_RESULT, clean_line, re.IGNORECASE)

        if not match:
            ErrorHandler.warn(f"Could not parse test line: {line.strip()}")
            return None

        time_str, test_name = match.groups()

        # Validate and parse execution time
        execution_time = Validator.validate_float(time_str, f"line: {line.strip()}")
        if execution_time is None:
            return None

        if not test_name or not test_name.strip():
            ErrorHandler.warn(f"Empty test name in line: {line.strip()}")
            return None

        return TestCase(test_name.strip(), matched_status, execution_time)

    @staticmethod
    def parse_test_name_components(test_name: str) -> Tuple[str, str]:
        """
        Parse test name into suite and class components.

        Args:
            test_name (str): Full test name to parse

        Returns:
            Tuple[str, str]: (suite_name, class_name)
        """
        test_parts = test_name.split("-")

        if len(test_parts) >= 3:
            # Format: prefix-suite-class-other
            return test_parts[1], test_parts[2]
        elif len(test_parts) == 2:
            # Format: suite-class
            return test_parts[0], test_parts[1]
        elif len(test_parts) == 1:
            # Format: testname (use as both suite and class)
            clean_name = test_parts[0].strip()
            return clean_name, clean_name
        else:
            # Fallback for unusual formats
            return "unknown", test_name

    @staticmethod
    def extract_total_time(line: str) -> Optional[float]:
        """
        Extract total execution time from a line.

        Args:
            line (str): Line that might contain total time information

        Returns:
            Optional[float]: Total time in seconds, or None if not found
        """
        match = re.search(Config.Patterns.TOTAL_TIME, line, re.IGNORECASE)

        if match:
            return Validator.validate_float(match.group(1), f"line: {line.strip()}")

        return None

    @staticmethod
    def extract_error_count(line: str) -> Optional[int]:
        """
        Extract error count from an error line.

        Args:
            line (str): Error line to parse

        Returns:
            Optional[int]: Error count if found, None otherwise
        """
        parts = line.split()
        for part in parts:
            if part.isdigit():
                try:
                    return int(part)
                except ValueError:
                    continue
        return None


class JUnitXMLGenerator:
    """Generator for JUnit XML format reports."""

    @staticmethod
    def sanitize_xml_content(text: str) -> str:
        """
        Sanitize text content for XML by removing invalid control characters.

        XML 1.0 does not allow control characters except tab (0x09), newline (0x0A), and carriage return (0x0D).
        This function removes other control characters that would cause XML parsing errors.
        Note: ElementTree automatically escapes XML entities (&, <, >, quotes) when setting text content,
        so we only need to remove invalid control characters here.

        Args:
            text: Text content that may contain invalid XML characters

        Returns:
            Sanitized text safe for XML
        """
        if not text:
            return text
        # Remove control characters except tab, newline, and carriage return
        # Valid XML 1.0 control chars: 0x09 (tab), 0x0A (newline), 0x0D (carriage return)
        sanitized = "".join(char if (ord(char) >= 0x20 or char in "\t\n\r") else "" for char in text)
        return sanitized

    @staticmethod
    def create_test_case_element(test_case: TestCase, test_name_components: Tuple[str, str]) -> ET.Element:
        """
        Create an XML element for a test case.

        Args:
            test_case (TestCase): Test case information
            test_name_components (Tuple[str, str]): (suite_name, class_name)

        Returns:
            ET.Element: XML element representing the test case
        """
        suite_name, class_name = test_name_components
        # Use the original test name as the testcase name, not the suite name
        # This ensures each test has a unique name in the XML output
        testcase = ET.Element(
            "testcase", name=test_case.name, classname=class_name, time=f"{test_case.execution_time:.3f}"
        )

        # Add failure element for failed tests
        if test_case.status == Config.Status.FAIL:
            failure = ET.SubElement(testcase, "failure")
            if test_case.error_message:
                failure.text = JUnitXMLGenerator.sanitize_xml_content(test_case.error_message)
            else:
                failure.text = f"{test_case.name} failed"
        elif test_case.status == Config.Status.FLAKY:
            # Mark flaky tests with a note
            system_out = ET.SubElement(testcase, "system-out")
            system_out.text = f"Test marked as flaky: {test_case.name}"

        return testcase

    @staticmethod
    def create_test_suite_element(suite_name: str, stats: TestStats) -> ET.Element:
        """
        Create a test suite XML element with statistics.

        Args:
            suite_name (str): Name of the test suite
            stats (TestStats): Test statistics

        Returns:
            ET.Element: Test suite XML element
        """
        return ET.Element(
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

    @staticmethod
    def format_xml(xml_element: ET.Element) -> str:
        """
        Format XML element with proper indentation.

        Args:
            xml_element (ET.Element): XML element to format

        Returns:
            str: Formatted XML string
        """
        rough_string = ET.tostring(xml_element, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        formatted_xml = reparsed.toprettyxml(indent="  ")

        # Remove extra blank lines that minidom creates
        lines = [line for line in formatted_xml.splitlines() if line.strip()]
        return "\n".join(lines) + "\n"

    @staticmethod
    def write_xml_report(testsuites: ET.Element, output_path: Union[str, Path]) -> None:
        """
        Write the JUnit XML test report to a file with proper formatting.

        Args:
            testsuites (ET.Element): XML structure containing the JUnit test report
            output_path (Union[str, Path]): Path where the JUnit XML report will be written
        """
        try:
            formatted_xml = JUnitXMLGenerator.format_xml(testsuites)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_xml)

        except (IOError, OSError) as e:
            ErrorHandler.fatal(f"Failed to write XML report to '{output_path}': {e}")

    @staticmethod
    def count_attachment_diagnostics(testsuites: ET.Element) -> Tuple[int, int]:
        """
        Count total testcases and how many have [[ATTACHMENT]] in system-out.
        Used for CI diagnostics so we can see whether attachments were written.
        """
        total = 0
        with_attachment = 0
        for suite in testsuites.findall("testsuite"):
            for tc in suite.findall("testcase"):
                total += 1
                system_out = tc.find("system-out")
                if system_out is not None and system_out.text and "[[ATTACHMENT]]" in (system_out.text or ""):
                    with_attachment += 1
        return total, with_attachment


class DisplayFormatter:
    """Utilities for formatting display output."""

    @staticmethod
    def get_status_display(status: str) -> str:
        """
        Get display string for test status.

        Args:
            status (str): Test status code

        Returns:
            str: Display string for status
        """
        return Config.Status.get_display_map().get(status, "UNKNOWN")

    @staticmethod
    def truncate_for_display(name: str, max_width: int, ellipsis: str = "...") -> str:
        """Truncate a string to max_width for aligned console output; keep the end so unique suffix is visible."""
        if len(name) <= max_width:
            return name
        return ellipsis + name[-(max_width - len(ellipsis)) :]

    @staticmethod
    def strip_common_prefix(names: List[str]) -> List[str]:
        """
        For console display only: split each name on hyphens and remove the common leading segments.
        e.g. if all names start with "tests-nativepython-testing-", that prefix is removed.
        """
        if not names:
            return []
        split_names = [name.split("-") for name in names]
        prefix_len = 0
        while prefix_len < min(len(s) for s in split_names):
            segment = split_names[0][prefix_len]
            if all(s[prefix_len] == segment for s in split_names):
                prefix_len += 1
            else:
                break
        if prefix_len == 0:
            return list(names)
        result = []
        for segments in split_names:
            suffix = "-".join(segments[prefix_len:])
            result.append(suffix if suffix else "-".join(segments))
        return result

    @staticmethod
    def print_separator(width: int = Config.Display.SUMMARY_WIDTH, char: str = "=") -> None:
        """Print a separator line."""
        print(char * width)

    @staticmethod
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

        # Count statuses
        status_counts = {}
        for test in test_cases:
            status_counts[test.status] = status_counts.get(test.status, 0) + 1

        # Print summary header
        print()
        DisplayFormatter.print_separator()
        print(f"TEST EXECUTION SUMMARY (Total: {len(test_cases)} tests, {total_time:.2f} seconds)")

        # Print status breakdown
        status_line = " | ".join(
            [f"{DisplayFormatter.get_status_display(status)}: {count}" for status, count in status_counts.items()]
        )
        print(f"Status breakdown: {status_line}")
        DisplayFormatter.print_separator()

        # Print table header
        print(
            f"{'TEST NAME':<{Config.Display.TEST_NAME_WIDTH}} "
            f"{'STATUS':<{Config.Display.STATUS_WIDTH}} "
            f"{'TIME (s)':<{Config.Display.TIME_WIDTH}} "
            f"{'% OF TOTAL':<{Config.Display.PERCENT_WIDTH}}"
        )
        DisplayFormatter.print_separator(char="-")

        # Strip common hyphen-separated prefix for display (e.g. tests-nativepython-testing-)
        names = [t.name for t in sorted_tests]
        shortened = DisplayFormatter.strip_common_prefix(names)
        name_to_display = dict(zip(names, shortened))

        # Print each test case (use shortened name, truncate if still long)
        for test in sorted_tests:
            percentage = (test.execution_time / total_time) * 100 if total_time > 0 else 0
            status_display = DisplayFormatter.get_status_display(test.status)
            display_name = DisplayFormatter.truncate_for_display(
                name_to_display[test.name], Config.Display.TEST_NAME_WIDTH
            )
            print(
                f"{display_name:<{Config.Display.TEST_NAME_WIDTH}} "
                f"{status_display:<{Config.Display.STATUS_WIDTH}} "
                f"{test.execution_time:.3f}s{percentage:>{Config.Display.PERCENT_WIDTH-1}.1f}%"
            )

        DisplayFormatter.print_separator()


def extract_kit_log_snippet(kit_log_path: Union[str, Path], max_bytes: int = 100 * 1024) -> str:
    """
    Extract from a kit log the blocks that do not start with [Info] or [Warning]
    (e.g. [Error], [Critical], and their multi-line continuations). Returns up to max_bytes
    from the end of that filtered content (most recent first). Standalone for testing/CLI.
    """
    kit_log_path = Path(kit_log_path)
    try:
        with open(kit_log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (IOError, OSError):
        return ""

    level_pattern = Config.Patterns.KIT_LOG_LEVEL
    blocks: List[str] = []
    current_block: List[str] = []
    include_current = False

    def is_block_starter(ln: str) -> bool:
        if level_pattern.search(ln):
            return True
        return (
            ln.startswith("[Info]")
            or ln.startswith("[Warning]")
            or ln.startswith("[Error]")
            or ln.startswith("[Critical]")
        )

    for line in lines:
        if is_block_starter(line):
            if current_block and include_current:
                blocks.append("".join(current_block))
            current_block = [line]
            include_current = "[Info]" not in line and "[Warning]" not in line
        else:
            current_block.append(line)

    if current_block and include_current:
        blocks.append("".join(current_block))

    combined = "".join(blocks)
    if len(combined) <= max_bytes:
        return combined
    return "... [truncated, showing last %d bytes] ...\n%s" % (max_bytes, combined[-max_bytes:])


class TestReportProcessor:
    """Main processor for test report generation."""

    def __init__(self, report_folder: Union[str, Path], suite_name: str):
        self.report_folder = Path(report_folder)
        self.suite_name = suite_name
        self.results_file_path = self.report_folder / Config.RESULTS_FILENAME

        # Check for full output file in the report folder
        self.full_output_file = self.report_folder / Config.FULL_OUTPUT_FILENAME
        if not self.full_output_file.exists():
            self.full_output_file = None

        self.parser = TestResultParser()
        self.xml_generator = JUnitXMLGenerator()
        self.error_details_map = {}
        # When a test has exactly one kit log, path (relative to repo root) for GitLab JUnit attachment
        self._kit_log_attachment_paths: Dict[str, str] = {}

    def validate_inputs(self) -> None:
        """Validate input files and directories exist."""
        if not Validator.validate_directory_exists(self.report_folder):
            ErrorHandler.fatal(f"Report folder '{self.report_folder}' does not exist")

        if not Validator.validate_file_exists(self.results_file_path):
            ErrorHandler.fatal(f"Test results file not found at '{self.results_file_path}'")

    def read_results_file(self) -> List[str]:
        """Read and return lines from the results file."""
        try:
            with open(self.results_file_path, "r", encoding="utf-8") as result_file:
                return result_file.readlines()
        except (IOError, OSError) as e:
            ErrorHandler.fatal(f"Failed to read results file '{self.results_file_path}': {e}")

    def parse_full_output_for_errors(self) -> Dict[str, str]:
        """
        Parse the full output file to extract detailed error messages for failed tests.

        Returns:
            Dict[str, str]: Mapping of test names to their error messages
        """
        if not self.full_output_file or not self.full_output_file.exists():
            return {}

        error_map = {}
        try:
            with open(self.full_output_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            capturing = False
            error_lines = []

            for line in lines:
                stripped = line.strip()

                # Look for test process failure marker
                if "[fail] test process failed." in stripped:
                    capturing = True
                    error_lines = []
                    continue

                # If capturing, look for ERROR and test name
                if capturing:
                    # Check if this is the end of error block
                    if re.search(r"-+\s+\[TEST PROCESS FAILED:", stripped):
                        # Extract test name from the end marker
                        match = re.search(r"\[TEST PROCESS FAILED:\s+([^\]]+)\]", stripped)
                        if match:
                            test_name = match.group(1).strip()
                            if error_lines:
                                error_map[test_name] = "\n".join(error_lines)
                        capturing = False
                        error_lines = []
                        continue

                    # Accumulate error lines
                    if stripped:
                        error_lines.append(stripped)

        except (IOError, OSError) as e:
            ErrorHandler.warn(f"Failed to read full output file '{self.full_output_file}': {e}")

        return error_map

    def process_test_results(self) -> Tuple[ET.Element, List[TestCase]]:
        """
        Parse test results from report file and generate JUnit XML structure.

        Returns:
            Tuple[ET.Element, List[TestCase]]: XML root element and list of TestCase objects
        """
        self.validate_inputs()

        # Parse error details from full output file if available
        self.error_details_map = self.parse_full_output_for_errors()
        if self.error_details_map:
            print(f"Loaded error details for {len(self.error_details_map)} failed tests from full output")

        testsuites = ET.Element("testsuites")
        testcases = []
        errors = []
        stats = TestStats()
        test_case_list = []

        lines = self.read_results_file()

        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()

            if not stripped_line:
                continue

            # Try to parse as test result line
            test_case = self.parser.parse_test_line(stripped_line)
            if test_case:
                base_name = self._get_base_name(test_case.name)
                # Expand script into one testcase per exttest block so each has a single log
                if base_name.startswith("tests-") and (
                    test_case.name.endswith(".sh") or test_case.name.endswith(".bat")
                ):
                    blocks = self._get_exttest_blocks_for_script(base_name)
                    if blocks:
                        block_time = test_case.execution_time / len(blocks) if blocks else 0.0
                        for subdir_name, _ in blocks:
                            block_case = TestCase(subdir_name, test_case.status, block_time)
                            self._process_test_case(block_case, stats, testcases, test_case_list)
                        continue
                self._process_test_case(test_case, stats, testcases, test_case_list)
                continue

            # Try to extract total time
            total_time = self.parser.extract_total_time(stripped_line)
            if total_time is not None:
                stats.total_time = total_time
                continue

            # Handle error lines
            if re.search(Config.Patterns.ERROR_LINE, stripped_line, re.IGNORECASE):
                self._process_error_line(stripped_line, stats, errors)

        # Create and populate test suite
        testsuite = self.xml_generator.create_test_suite_element(self.suite_name, stats)

        # Add error information if errors exist
        if errors:
            error_node = ET.SubElement(testsuite, "system-err")
            error_node.text = "\n".join(errors)

        testsuite.extend(testcases)
        testsuites.append(testsuite)

        return testsuites, test_case_list

    def _get_base_name(self, test_name: str) -> str:
        """Strip script extension from test name (e.g. tests-foo.sh -> tests-foo)."""
        base = test_name
        if test_name.endswith(".bat"):
            base = test_name[:-4]
        elif test_name.endswith(".sh"):
            base = test_name[:-3]
        return base

    def _get_failure_log_path(self, test_name: str) -> Optional[Path]:
        """Return path to the per-test log file if it exists (e.g. nativepython tee logs)."""
        base_name = self._get_base_name(test_name)
        found = self._find_main_log_for_test(base_name)
        return found

    def _find_main_log_for_test(self, base_name: str) -> Optional[Path]:
        """
        Find the main .log file for a test. All lookups are under report_folder (_testoutput); intermediate is for coverage only.
        Tries multiple layouts so exttest and nativepython both work:
        - Exact: report_folder / (base_name + ".log") e.g. tests-startup-full.log
        - Flat: if base_name contains '/', try report_folder / (last segment + ".log")
          e.g. doc_snippets/tests-nativepython-... -> tests-nativepython-....log (tee uses basename)
        - Recursive: any .log under report_folder whose relative path (no .log) equals base_name
          or whose filename stem equals the last segment of base_name (single match).
        """
        report = self.report_folder
        # 1) Exact: base_name.log (at root of report folder)
        candidate = report / f"{base_name}.log"
        if candidate.exists():
            return candidate
        # 2) Flat: test name has path (e.g. doc_snippets/tests-nativepython-...); log may be flat as basename.log
        if "/" in base_name:
            last_segment = base_name.split("/")[-1]
            candidate = report / f"{last_segment}.log"
            if candidate.exists():
                return candidate
        # 3) Recursive: any **/*.log whose stem (or relative path without .log) matches
        try:
            matches: List[Path] = []
            for log_path in report.rglob("*.log"):
                if log_path.is_file():
                    try:
                        rel = log_path.relative_to(report)
                    except ValueError:
                        continue
                    stem_path = str(rel.with_suffix("")).replace("\\", "/")
                    stem_name = rel.stem
                    if stem_path == base_name or stem_name == base_name:
                        return log_path
                    if "/" in base_name and stem_name == base_name.split("/")[-1]:
                        matches.append(log_path)
            if len(matches) == 1:
                return matches[0]
        except OSError:
            pass
        # 4) Exttest block: test name is the subdir name (e.g. exttest_omni_isaac_core_archive-startup) -> log inside that subdir
        subdir = report / base_name
        if subdir.is_dir():
            logs = sorted(subdir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            primary = None
            for log in logs:
                if log.stem.endswith("_0"):
                    primary = log
                    break
            if primary is None and logs:
                primary = logs[0]
            if primary is not None:
                return primary
        # 5) Exttest layout: script tests-<name>.sh -> subdirs exttest_<name>, exttest_<name>-startup, etc.
        exttest_logs = self._find_exttest_log_paths(base_name)
        if exttest_logs:
            return exttest_logs[0]
        return None

    def _get_exttest_blocks_for_script(self, script_base_name: str) -> List[Tuple[str, Path]]:
        """
        For a script (e.g. tests-omni.isaac.core_archive), return one (subdir_name, log_path) per exttest block
        so we can emit one testcase per block with a single log each.
        """
        log_paths = self._find_exttest_log_paths(script_base_name)
        out: List[Tuple[str, Path]] = []
        for log_path in log_paths:
            if log_path.parent.is_dir() and log_path.parent.parent == self.report_folder:
                out.append((log_path.parent.name, log_path))
        return out

    def _find_exttest_log_paths(self, base_name: str) -> List[Path]:
        """
        For exttest runs, script name is tests-<ext>.<name>.sh; logs live in
        report_folder (_testoutput)/exttest_<ext>_<name>*/<log>.log (dots in name become underscores in dir).
        All test result files and exttest logs are under _testoutput; intermediate dirs are for coverage only.
        Return one primary log per matching subdir.
        """
        report = self.report_folder
        if not base_name.startswith("tests-"):
            return []
        # exttest subdirs use underscores (e.g. exttest_omni_isaac_core_archive not exttest_omni.isaac.core_archive)
        prefix = "exttest_" + base_name[6:].replace(".", "_")
        out: List[Path] = []
        try:
            for child in report.iterdir():
                if not child.is_dir() or not child.name.startswith(prefix):
                    continue
                # Prefer *_<timestamp>_0.log, else most recent .log in subdir
                logs = sorted(child.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
                primary = None
                for log in logs:
                    if log.stem.endswith("_0"):
                        primary = log
                        break
                if primary is None and logs:
                    primary = logs[0]
                if primary is not None:
                    out.append(primary)
        except OSError:
            pass
        return out

    def _find_main_log_paths_for_test(self, base_name: str) -> List[Path]:
        """Return all main log paths for this test (one for nativepython, multiple for exttest)."""
        # exttest_log_paths only handles base_name starting with "tests-"; when we have a block name
        # (e.g. exttest_isaacsim_ros2_bridge) we must resolve by subdir explicitly
        if base_name.startswith("exttest_"):
            subdir = self.report_folder / base_name
            if subdir.is_dir():
                logs = sorted(subdir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
                primary = None
                for log in logs:
                    if log.stem.endswith("_0"):
                        primary = log
                        break
                if primary is None and logs:
                    primary = logs[0]
                if primary is not None:
                    return [primary]
            return []
        exttest = self._find_exttest_log_paths(base_name)
        if exttest:
            return exttest
        single = self._find_main_log_for_test(base_name)
        if single is not None:
            return [single]
        return []

    def _extract_carb_log_paths(self, log_path: Path) -> List[str]:
        """Parse a test log file for '[Info] [carb] Logging to file:' lines and return the paths."""
        paths: List[str] = []

        def extract_from_content(content: str) -> List[str]:
            found: List[str] = []
            for line in content.splitlines():
                match = re.search(Config.Patterns.CARB_LOGGING_LINE, line)
                if not match:
                    match = Config.Patterns.CARB_LOGGING_LINE_RELAXED.search(line)
                if match:
                    raw = match.group(1).strip()
                    raw = raw.replace("\u00a0", " ")
                    if raw and not raw.isspace():
                        found.append(raw)
            return found

        encodings = ["utf-8", "utf-16", "utf-16-le", "cp1252"]
        try:
            for enc in encodings:
                try:
                    with open(log_path, "r", encoding=enc, errors="replace") as f:
                        paths = extract_from_content(f.read())
                except (UnicodeError, UnicodeDecodeError):
                    continue
                if paths:
                    break
            if not paths:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    paths = extract_from_content(f.read())
        except (IOError, OSError) as e:
            ErrorHandler.warn(f"Failed to read log file '{log_path}' for carb log paths: {e}")
        return paths

    def _extract_kit_log_snippet(self, kit_log_path: Path, max_bytes: int = 100 * 1024) -> str:
        """Delegate to module-level function for reuse (e.g. --extract-snippet CLI)."""
        return extract_kit_log_snippet(kit_log_path, max_bytes)

    def _normalize_log_to_utf8(self, log_path: Path) -> None:
        """
        If the file is UTF-16 (e.g. from Windows Tee-Object), re-write it as UTF-8 so the rest
        of the report pipeline reads it consistently (aligns with Linux tee output).
        """
        try:
            with open(log_path, "rb") as f:
                bom = f.read(2)
            if len(bom) < 2:
                return
            if bom == b"\xff\xfe":
                encoding = "utf-16-le"
            elif bom == b"\xfe\xff":
                encoding = "utf-16-be"
            else:
                return
            with open(log_path, "r", encoding=encoding, errors="replace") as f:
                content = f.read()
            with open(log_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
        except (IOError, OSError) as e:
            ErrorHandler.warn(f"Failed to normalize log encoding for '{log_path}': {e}")

    def _find_repo_root(self) -> Optional[Path]:
        """Walk up from report folder to find repo root (directory containing repo.toml or .git).
        If not found from report_folder (e.g. report is under an extracted package), try from cwd so
        attachment paths are still emitted for GitLab."""
        current = self.report_folder.resolve()
        for _ in range(20):
            if (current / "repo.toml").exists() or (current / ".git").exists():
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent
        # Fallback: repo root not above report_folder (e.g. from-package run); try cwd
        try:
            current = Path.cwd().resolve()
            for _ in range(20):
                if (current / "repo.toml").exists() or (current / ".git").exists():
                    return current
                parent = current.parent
                if parent == current:
                    break
                current = parent
        except (OSError, RuntimeError):
            pass
        return None

    def _move_carb_logs_to_testoutput_from_folder(self) -> None:
        """
        Scan the report folder for test .log files, find '[Info] [carb] Logging to file:' lines,
        move those kit logs into the report folder, and append paths to each .log file.
        Runs before process_test_results() so the appended content is included when we read
        .log files for the JUnit XML failure details.
        Processes both root-level *.log and logs inside exttest_* subdirs so kit log attachments
        work for exttest blocks (keyed by subdir name, e.g. exttest_omni_isaac_core_archive-startup).
        """
        repo_root = self._find_repo_root()
        # Root-level .log files (e.g. nativepython runs)
        for log_path in sorted(self.report_folder.glob("*.log")):
            stem = log_path.stem
            if stem.endswith("-kit") or "-kit-" in stem:
                continue
            self._normalize_log_to_utf8(log_path)
            self._process_one_log_for_carb(log_path, repo_root, attachment_key=None)
        # exttest_* subdirs: process each .log so kit log is keyed by block name for attachments
        try:
            for child in sorted(self.report_folder.iterdir()):
                if not child.is_dir() or not child.name.startswith("exttest_"):
                    continue
                for log_path in sorted(child.glob("*.log")):
                    if log_path.stem.endswith("-kit") or "-kit-" in log_path.stem:
                        continue
                    self._normalize_log_to_utf8(log_path)
                    self._process_one_log_for_carb(log_path, repo_root, attachment_key=child.name)
        except OSError:
            pass

    def _process_one_log_for_carb(
        self, log_path: Path, repo_root: Optional[Path], attachment_key: Optional[str] = None
    ) -> None:
        """Move kit logs referenced in one test .log file. attachment_key is the name used for JUnit attachment lookup (default: log stem, or exttest block name for exttest_* logs)."""
        base_name = attachment_key if attachment_key is not None else log_path.stem
        carb_paths = self._extract_carb_log_paths(log_path)
        print(f"[carb log] Processing '{base_name}' (log: {log_path}), extracted {len(carb_paths)} carb path(s)")
        moved_dests: List[Path] = []
        log_path_resolved = log_path.resolve()
        for i, src in enumerate(carb_paths):
            src_path = Path(src)
            # Do not move the log file we're reading: exttest logs often log their own path, so moving would remove the main test log and break JUnit attachments.
            if src_path.resolve() == log_path_resolved:
                print(f"[carb log]   [{i + 1}] {src_path} -> skip (same as current log)")
                continue
            exists = src_path.exists()
            print(f"[carb log]   [{i + 1}] {src_path} -> exists: {exists}")
            if not exists:
                continue
            if len(carb_paths) == 1:
                dest_name = f"{base_name}-kit.log"
            else:
                dest_name = f"{base_name}-kit-{i}.log"
            # Keep kit log next to the test log (exttest_* subdir) or at report root
            dest_parent = log_path.parent if log_path.parent != self.report_folder else self.report_folder
            dest = dest_parent / dest_name
            try:
                shutil.move(str(src_path), str(dest))
                moved_dests.append(dest)
                print(f"[carb log]   Moved to {dest}")
            except (IOError, OSError) as e:
                ErrorHandler.warn(f"Failed to move carb log '{src_path}' to '{dest}': {e}")
        if moved_dests:
            # Kit log paths/snippets are no longer appended to the main .log (was too long). Links via JUnit attachment only.
            if len(moved_dests) == 1:
                att_path_str: Optional[str] = None
                if repo_root:
                    try:
                        att_path = moved_dests[0].resolve().relative_to(repo_root.resolve())
                        att_path_str = str(att_path).replace("\\", "/")
                    except ValueError:
                        pass
                if att_path_str is None:
                    try:
                        rel = moved_dests[0].resolve().relative_to(self.report_folder.resolve())
                        att_path_str = str(rel).replace("\\", "/")
                    except ValueError:
                        pass
                if att_path_str:
                    self._kit_log_attachment_paths[base_name] = att_path_str
        elif carb_paths:
            print(f"[carb log]   No kit log(s) moved (sources not found), not appending to {log_path}")

    def _process_test_case(
        self, test_case: TestCase, stats: TestStats, testcases: List[ET.Element], test_case_list: List[TestCase]
    ) -> None:
        """Process a parsed test case."""
        # Parse test name components
        suite_comp, class_comp = self.parser.parse_test_name_components(test_case.name)
        # For exttest block (subdir name like exttest_omni_isaac_core_archive-startup), classname = extension name
        if test_case.name.startswith("exttest_"):
            ext_id = test_case.name[8:].split("-")[0]  # drop "exttest_" and any "-startup" suffix
            parts = ext_id.split("_", 2)  # e.g. omni_isaac_core_archive -> ["omni", "isaac", "core_archive"]
            class_comp = ".".join(parts) if parts else test_case.name
        # For exttest script (tests-<ext>.sh/.bat), classname = extension name without script extension
        elif test_case.name.startswith("tests-") and (
            test_case.name.endswith(".sh") or test_case.name.endswith(".bat")
        ):
            class_comp = self._get_base_name(test_case.name)[
                6:
            ]  # "tests-omni.isaac.core_archive" -> "omni.isaac.core_archive"

        # Update statistics
        stats.update_for_status(test_case.status)

        # If this is a failed test, attach error details: prefer per-test log file, then full output
        enhanced_test_case = test_case
        if test_case.status == Config.Status.FAIL:
            error_detail = None
            log_path = self._get_failure_log_path(test_case.name)
            if log_path:
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                        # Limit error detail to last 50KB to avoid bloating JUnit XML
                        max_size = 50 * 1024
                        if len(content) > max_size:
                            error_detail = "... [truncated] ...\n" + content[-max_size:]
                        else:
                            error_detail = content
                        # Sanitize content to remove invalid XML characters
                        error_detail = JUnitXMLGenerator.sanitize_xml_content(error_detail)
                except (IOError, OSError) as e:
                    ErrorHandler.warn(f"Failed to read log file '{log_path}': {e}")
            if not error_detail and self.error_details_map:
                error_detail = self.error_details_map.get(test_case.name)
                if error_detail:
                    # Sanitize content from full output file as well
                    error_detail = JUnitXMLGenerator.sanitize_xml_content(error_detail)
            if error_detail:
                enhanced_test_case = TestCase(test_case.name, test_case.status, test_case.execution_time, error_detail)

        # Create XML element
        testcase_element = self.xml_generator.create_test_case_element(enhanced_test_case, (suite_comp, class_comp))
        # GitLab JUnit attachments: main test log(s) (exttest/nativepython) and optionally kit log (nativepython, when exactly one)
        base_name = self._get_base_name(test_case.name)
        main_log_paths = self._find_main_log_paths_for_test(base_name)
        if not test_case_list:
            print(
                f"Diagnostics: in _process_test_case first test base_name={base_name!r} main_log_paths={len(main_log_paths)}"
            )
        attachment_lines: List[str] = []
        repo_root = self._find_repo_root()
        for main_log_path in main_log_paths:
            rel_path: Optional[str] = None
            if repo_root:
                try:
                    rel = main_log_path.resolve().relative_to(repo_root.resolve())
                    rel_path = str(rel).replace(os.sep, "/")
                except ValueError:
                    pass
            if rel_path is None:
                # Log outside repo_root (e.g. from-package extract) or repo_root was None: use path relative to report_folder
                try:
                    rel = main_log_path.resolve().relative_to(self.report_folder.resolve())
                    rel_path = str(rel).replace(os.sep, "/")
                except ValueError:
                    pass
            if rel_path:
                attachment_lines.append(f"[[ATTACHMENT|{rel_path}]]")
        kit_attachment_path = self._kit_log_attachment_paths.get(base_name)
        if kit_attachment_path:
            attachment_lines.append(f"[[ATTACHMENT|{kit_attachment_path}]]")
        if attachment_lines:
            attachment_text = "\n".join(attachment_lines)
            existing = testcase_element.find("system-out")
            if existing is not None:
                existing.text = (existing.text or "").rstrip() + "\n" + attachment_text
            else:
                system_out = ET.SubElement(testcase_element, "system-out")
                system_out.text = attachment_text
        testcases.append(testcase_element)

        # Store for summary (use full test name so display shows e.g. tests-nativepython-testing-... not just "nativepython.testing")
        test_case_list.append(TestCase(test_case.name, test_case.status, test_case.execution_time))

    def _process_error_line(self, line: str, stats: TestStats, errors: List[str]) -> None:
        """Process an error line."""
        if stats.error == 0:
            error_count = self.parser.extract_error_count(line)
            if error_count is not None:
                stats.error = error_count
        errors.append(line)


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
        ErrorHandler.error("Missing required arguments")
        print("Usage: python standalone_report.py <report_folder_path> <suite_name>")
        sys.exit(1)

    try:
        # Extract arguments
        report_folder = os.path.abspath(args.extra_args[0])
        suite_name = args.extra_args[1]

        # Process test results
        print(f"Processing report folder: {report_folder}")
        print(f"Suite name: {suite_name}")

        # Create processor and process results
        processor = TestReportProcessor(report_folder, suite_name)

        # Diagnostics: repo root (affects attachment path resolution)
        repo_root = processor._find_repo_root()
        print(f"Diagnostics: repo_root = {repo_root if repo_root else 'not found'}")

        # Move carb/kit logs and append paths to test .log files before we read them for the XML
        processor._move_carb_logs_to_testoutput_from_folder()

        # Diagnostics: kit log attachments registered (for JUnit [[ATTACHMENT]] lines)
        kit_keys = list(processor._kit_log_attachment_paths.keys())
        n_kit = len(kit_keys)
        if n_kit:
            print(
                f"Diagnostics: kit log attachments registered for {n_kit} test(s): {kit_keys[:10]}{' ...' if n_kit > 10 else ''}"
            )
        else:
            print("Diagnostics: no kit log attachments registered")

        testsuites, test_cases = processor.process_test_results()

        # Write XML report
        output_path = processor.report_folder / Config.OUTPUT_FILENAME
        print(f"Writing JUnit XML report to: {output_path}")
        JUnitXMLGenerator.write_xml_report(testsuites, output_path)

        # Diagnostics: how many testcases have [[ATTACHMENT]] in system-out (for CI visibility)
        total_tc, with_att = JUnitXMLGenerator.count_attachment_diagnostics(testsuites)
        print(f"JUnit report: {with_att} testcase(s) with [[ATTACHMENT]] in system-out (of {total_tc} total)")
        if test_cases:
            first_base = processor._get_base_name(test_cases[0].name)
            n_paths = len(processor._find_main_log_paths_for_test(first_base))
            print(f"Diagnostics: first test base_name={first_base!r} main_log_paths={n_paths}")

        # Always print test summary
        DisplayFormatter.print_test_summary(test_cases)

        print("Report generation complete")

        # Check if the test summary has any failures
        failed_tests = [test for test in test_cases if test.status == Config.Status.FAIL]
        if failed_tests:
            print(f"Test summary has {len(failed_tests)} failures")
            sys.exit(1)

    except Exception as e:
        ErrorHandler.handle_exception(e, "generating JUnit XML report")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert test results to JUnit XML format for CI reporting and test visualization"
    )
    parser.add_argument("extra_args", nargs="*", help="Additional arguments: <report_folder_path> <suite_name>")
    parser.add_argument(
        "--extract-snippet",
        metavar="KIT_LOG",
        help="Test mode: extract non-Info/non-Warning snippet from a kit log file and print to stdout",
    )

    args = parser.parse_args()

    if args.extract_snippet:
        path = Path(args.extract_snippet)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        print(extract_kit_log_snippet(path))
        sys.exit(0)

    main(args)
