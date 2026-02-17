import csv
import re
from collections import namedtuple

import xlsxwriter


class Column:
    URL_NAME = 0
    PARENT_NAME = 1
    BASE = 2
    RESULT = 3
    WARNING_STRING = 4
    INFO_STRING = 5
    VALID = 6
    URL = 7
    LINE = 8
    COLUMN = 9
    NAME = 10
    DL_TIME = 11
    SIZE = 12
    CHECK_TIME = 13
    CACHED = 14
    LEVEL = 15
    MODIFIED = 16


HEADERS = [
    "Assignee",
    "Link URL",
    "Page URL",
    "Link Alt Text",
    "Line",
    "Column",
    "Result",
]


def get_assignee(url):
    Assignee = namedtuple("Assignee", ["regex_pattern", "team"])

    # Assignees should be ordered by priority (the first match is assigned)
    assignees = [
        Assignee("isaacsim", "IsaacSim"),
        Assignee("carbonite", "Carbonite"),
        Assignee("isaacsim", "IsaacSim"),
        Assignee("usd", "USD"),
        Assignee("omni\.?graph", "OmniGraph"),
        Assignee("ogn", "OmniGraph"),
        Assignee("kit\/docs", "Kit"),
    ]

    for assignee in assignees:
        print(assignee.regex_pattern, url)
        if re.search(assignee.regex_pattern, url):
            return assignee.team

    return "OmniDocs"


def write_to_xlsx(rows):
    workbook = xlsxwriter.Workbook("linkcheck_results.xlsx")
    worksheet = workbook.add_worksheet("Broken Links")

    # Set column width.
    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, 1, 100)
    worksheet.set_column(2, 2, 100)
    worksheet.set_column(3, 3, 30)
    worksheet.set_column(6, 6, 50)

    # Create title cell.
    format_ = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#EFEFEF",
            "font_size": 16,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }
    )
    SHEET_NAME = "Broken Links in Omniverse Documentation"
    worksheet.merge_range(0, 0, 0, 6, SHEET_NAME, format_)

    # Create header row.
    format_ = workbook.add_format(
        {
            "bold": True,
            "border": 1,
            "align": "center",
        }
    )
    worksheet.write_row("A2", HEADERS, format_)

    # Write data.
    for idx, row in enumerate(rows, 2):
        print(row)
        worksheet.write_row(
            idx,
            0,
            [
                get_assignee(row[Column.PARENT_NAME]),
                row[Column.URL],
                row[Column.PARENT_NAME],
                row[Column.NAME],
                row[Column.LINE],
                row[Column.COLUMN],
                f"{row[Column.RESULT][:45]}..." if len(row[Column.RESULT]) > 45 else row[Column.RESULT],
            ],
        )

    workbook.close()


if __name__ == "__main__":
    with open("linkchecker-out.csv", "r") as oldfile:
        rows = list(csv.reader(oldfile))[4:-1]
        write_to_xlsx(rows)
