import argparse
import datetime
import os
import platform
import re
import xml.etree.ElementTree as ET
from datetime import datetime


class Stats:
    passed: int = 0
    failure: int = 0
    error: int = 0
    skipped: int = 0
    total_time: float = 0

    def get_total(self):
        return self.passed + self.failure + self.error + self.skipped


def main(args: argparse.Namespace):
    print(args.extra_args)
    report_folder = os.path.abspath(args.extra_args[0])
    suite_name = args.extra_args[1]
    print(report_folder)
    testsuites = ET.Element("testsuites")
    testcases = []
    errors = []
    stats = Stats()
    with open(os.path.join(report_folder, "repo_test_results.txt")) as my_file:
        # print(my_file.read())
        lines = my_file.readlines()

        for line in lines:
            if any(status in line for status in ["[   ok   ]", "[retry ok]", "[  fail  ]", "[ flaky ]"]):
                input = line.replace(" ", "").strip()
                result = re.split(r"\[(retryok|ok|flaky|fail)\]\[(.*)s\](\[.*\])?(.*)", input)
                result = list(filter(None, result))
                # print(result)

                if len(result) == 3:
                    full_name = result[2]
                else:
                    full_name = result[3]

                test_data = full_name.split("-")
                # print(test_data)
                if len(test_data) == 3:
                    suite = test_data[1]
                    classname = test_data[2]
                else:
                    suite = "pythontests"
                    classname = test_data[1]
                # print(test_data)
                testcase = ET.Element("testcase", name=suite, classname=classname, time=f"{float(result[1]):.3f}")
                if result[0] == "fail":
                    stats.failure += 1
                    node = ET.SubElement(testcase, "failure")
                    node.text = f"{full_name} failed"
                else:
                    stats.passed += 1
                testcases.append(testcase)
            if "total time" in line:
                result = list(filter(None, re.split(r"(total time:)\s(.*)s", line)))
                stats.total_time = float(result[1])
            elif "[ERROR]" in line:
                if stats.error == 0:
                    stats.error = int(line.split()[1])
                errors.append(line)

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
        if len(errors) > 0:
            node = ET.SubElement(testsuite, "error")
            node.text = "{}".format("".join(errors[0:]))
        testsuite.extend(testcases)
        testsuites.append(testsuite)

    output_path = os.path.join(report_folder, "results.xml")
    print("writing report to: ", output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ET.tostring(testsuites, encoding="unicode", xml_declaration=True))
