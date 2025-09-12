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
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union


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
            return {
                cls.PASS: "PASS",
                cls.FAIL: "FAIL",
                cls.FLAKY: "FLAKY",
                cls.RETRY_OK: "RETRY_OK"
            }
    
    # File patterns
    RESULTS_FILENAME = "repo_test_results.txt"
    OUTPUT_FILENAME = "results.xml"
    
    # Regex patterns
    class Patterns:
        # Status pattern mapping  
        STATUS_PATTERNS = [
            (r"\[\s*ok\s*\]", "ok"),
            (r"\[\s*retry\s*ok\s*\]", "retryok"),
            (r"\[\s*fail\s*\]", "fail"),
            (r"\[\s*flaky\s*\]", "flaky")
        ]
        
        # Test result extraction pattern
        TEST_RESULT = r"\[(?:retryok|ok|flaky|fail)\]\[([0-9.]+)s\](?:\[[^\]]*\])?(.*)"
        
        # Total time extraction pattern  
        TOTAL_TIME = r"total\s+time:\s*([0-9.]+)s"
        
        # Error line pattern
        ERROR_LINE = r"\[ERROR\]"
    
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
        clean_line = re.sub(r'\s+', '', line)  # Remove all whitespace
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
            "testcase",
            name=test_case.name,
            classname=class_name,
            time=f"{test_case.execution_time:.3f}"
        )
        
        # Add failure element for failed tests
        if test_case.status == Config.Status.FAIL:
            failure = ET.SubElement(testcase, "failure")
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
        rough_string = ET.tostring(xml_element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        formatted_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove extra blank lines that minidom creates
        lines = [line for line in formatted_xml.splitlines() if line.strip()]
        return '\n'.join(lines) + '\n'
    
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
        status_line = " | ".join([
            f"{DisplayFormatter.get_status_display(status)}: {count}" 
            for status, count in status_counts.items()
        ])
        print(f"Status breakdown: {status_line}")
        DisplayFormatter.print_separator()
        
        # Print table header
        print(f"{'TEST NAME':<{Config.Display.TEST_NAME_WIDTH}} "
              f"{'STATUS':<{Config.Display.STATUS_WIDTH}} "
              f"{'TIME (s)':<{Config.Display.TIME_WIDTH}} "
              f"{'% OF TOTAL':<{Config.Display.PERCENT_WIDTH}}")
        DisplayFormatter.print_separator(char="-")

        # Print each test case
        for test in sorted_tests:
            percentage = (test.execution_time / total_time) * 100 if total_time > 0 else 0
            status_display = DisplayFormatter.get_status_display(test.status)
            print(f"{test.name:<{Config.Display.TEST_NAME_WIDTH}} "
                  f"{status_display:<{Config.Display.STATUS_WIDTH}} "
                  f"{test.execution_time:.3f}s{percentage:>{Config.Display.PERCENT_WIDTH-1}.1f}%")

        DisplayFormatter.print_separator()


class TestReportProcessor:
    """Main processor for test report generation."""
    
    def __init__(self, report_folder: Union[str, Path], suite_name: str):
        self.report_folder = Path(report_folder)
        self.suite_name = suite_name
        self.results_file_path = self.report_folder / Config.RESULTS_FILENAME
        self.parser = TestResultParser()
        self.xml_generator = JUnitXMLGenerator()
    
    def validate_inputs(self) -> None:
        """Validate input files and directories exist."""
        if not Validator.validate_directory_exists(self.report_folder):
            ErrorHandler.fatal(f"Report folder '{self.report_folder}' does not exist")
        
        if not Validator.validate_file_exists(self.results_file_path):
            ErrorHandler.fatal(f"Test results file not found at '{self.results_file_path}'")
    
    def read_results_file(self) -> List[str]:
        """Read and return lines from the results file."""
        try:
            with open(self.results_file_path, 'r', encoding='utf-8') as result_file:
                return result_file.readlines()
        except (IOError, OSError) as e:
            ErrorHandler.fatal(f"Failed to read results file '{self.results_file_path}': {e}")
    
    def process_test_results(self) -> Tuple[ET.Element, List[TestCase]]:
        """
        Parse test results from report file and generate JUnit XML structure.

        Returns:
            Tuple[ET.Element, List[TestCase]]: XML root element and list of TestCase objects
        """
        self.validate_inputs()
        
        testsuites = ET.Element("testsuites")
        testcases = []
        errors = []
        stats = TestStats()
        test_case_list = []
        
        lines = self.read_results_file()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Try to parse as test result line
            test_case = self.parser.parse_test_line(line)
            if test_case:
                self._process_test_case(test_case, stats, testcases, test_case_list)
                continue

            # Try to extract total time
            total_time = self.parser.extract_total_time(line)
            if total_time is not None:
                stats.total_time = total_time
                continue

            # Handle error lines
            if re.search(Config.Patterns.ERROR_LINE, line, re.IGNORECASE):
                self._process_error_line(line, stats, errors)
        
        # Create and populate test suite
        testsuite = self.xml_generator.create_test_suite_element(self.suite_name, stats)
        
        # Add error information if errors exist
        if errors:
            error_node = ET.SubElement(testsuite, "system-err")
            error_node.text = "\n".join(errors)
        
        testsuite.extend(testcases)
        testsuites.append(testsuite)
        
        return testsuites, test_case_list
    
    def _process_test_case(self, test_case: TestCase, stats: TestStats, 
                          testcases: List[ET.Element], test_case_list: List[TestCase]) -> None:
        """Process a parsed test case."""
        # Parse test name components
        suite_comp, class_comp = self.parser.parse_test_name_components(test_case.name)
        
        # Update statistics
        stats.update_for_status(test_case.status)
        
        # Create XML element
        testcase_element = self.xml_generator.create_test_case_element(
            test_case, (suite_comp, class_comp)
        )
        testcases.append(testcase_element)
        
        # Store for summary
        full_test_name = f"{suite_comp}.{class_comp}"
        test_case_list.append(TestCase(full_test_name, test_case.status, test_case.execution_time))
    
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
        testsuites, test_cases = processor.process_test_results()

        # Write XML report
        output_path = processor.report_folder / Config.OUTPUT_FILENAME
        print(f"Writing JUnit XML report to: {output_path}")
        JUnitXMLGenerator.write_xml_report(testsuites, output_path)

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

    args = parser.parse_args()
    main(args)
