"""This script is used to generate release notes from JIRA.
author: Andrew Grant <agrant@nvidia.com>

It generates RST text following the style guidance for Release Notes.

Release Notes come from the "Release Notes" field in Jira.

Release Notes text can use Conventional Commits to set type and scope: https://www.conventionalcommits.org/en/v1.0.0/

Falls back to using issue type and development team for type/scope.
"""

import argparse
import os
import pickle
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import Optional

from jira import JIRA, Issue

JIRA_SERVER = "https://jirasw.nvidia.com/"
RELEASE_NOTE_FIELD = "customfield_23203"
DEV_TEAM_FIELD = "customfield_37300"
JIRA_CACHE = Path("jira.data.pickle")
DEFAULT_JQL = "filter=127763"  # current kit sdk release notes


@dataclass
class MyJira:
    key: str
    issue_type: str
    summary: str
    fix_versions: list[str]
    affects_versions: list[str]
    development_team: str
    release_notes: str

    @staticmethod
    def from_issue(issue: Issue):
        issue_type = issue.fields.issuetype.name
        fix_versions = [version.name for version in getattr(issue.fields, "fixVersions", [])]
        affects_versions = [version.name for version in getattr(issue.fields, "affectsVerions", [])]
        development_team = getattr(issue.fields, DEV_TEAM_FIELD, None)
        if development_team is not None:
            development_team = development_team.value
        else:
            development_team = ""

        release_notes = getattr(issue.fields, RELEASE_NOTE_FIELD, "")
        return MyJira(
            issue.key,
            issue_type,
            issue.fields.summary,
            fix_versions,
            affects_versions,
            development_team,
            release_notes,
        )

    @staticmethod
    def from_issues(issue_list: list[Issue]):
        for issue in issue_list:
            yield MyJira.from_issue(issue)


class NoteType(StrEnum):
    """
    Added: New features.
    Fixed: Specifically related to the resolution of bugs.
    Improved: Update that increases the quality of the product but does not fit in another type.
    Security: Denotes changes/fixes to security.
    Deprecated: Planned for removal in a future version.
    Removed: Features, UI, etc.
    """

    ADDED = auto()
    FIXED = auto()
    IMPROVED = auto()
    SECURITY = auto()
    DEPRECATED = auto()
    REMOVED = auto()


def parse_conventional_commit(commit_message: str) -> dict:
    """
    Parses a Conventional Commit message based on Conventional Commits 1.0.0 specification.

    :param commit_message: The full commit message as a string.
    :return: A dictionary containing the type, scope, description, body, and footer (if any).
    """
    # Regex to capture type, scope, and description
    pattern = r"^(?:(?P<type>[a-zA-Z0-9\-]+)?(\((?P<scope>[^\)]+)\))?!?:\s*)?(?P<description>[^\n]+)(\n\n(?P<body>[\s\S]*?))?(\n\n(?P<footer>[\s\S]*))?$"
    match = re.match(pattern, commit_message)

    if not match:
        raise ValueError("The commit message does not conform to the Conventional Commits spec.")

    commit_dict = match.groupdict()

    # Split the commit message into lines
    lines = commit_message.strip().split("\n")

    # Extract body and footer, which are separated from the header by a blank line
    if len(lines) > 1:
        # Find the index of the first blank line after the header
        try:
            body_start_index = lines.index("", 1) + 1
            body_lines = lines[body_start_index:]
        except ValueError:
            body_lines = lines[1:]  # If no blank line, treat everything as body

        # Separate body and footer (footer usually starts with "BREAKING CHANGE:" or references like "Closes #123")
        footer_index = next(
            (
                i
                for i, line in enumerate(body_lines)
                if line.startswith("BREAKING CHANGE") or re.match(r"(Closes|Fixes|Refs) #[0-9]+", line)
            ),
            None,
        )

        if footer_index is not None:
            commit_dict["body"] = "\n".join(body_lines[:footer_index]).strip()
            commit_dict["footer"] = "\n".join(body_lines[footer_index:]).strip()
        else:
            commit_dict["body"] = "\n".join(body_lines).strip()
            commit_dict["footer"] = None
    else:
        commit_dict["body"] = None
        commit_dict["footer"] = None

    return commit_dict


@dataclass
class ReleaseNote:
    description: str
    type: str
    jira_key: str
    scope: Optional[str] = None
    body: Optional[str] = None
    footer: Optional[str] = None

    @staticmethod
    def from_my_jira(my_jira: MyJira):

        def _note_scope_from_jira():
            return my_jira.development_team

        def _note_type_from_jira():
            if my_jira.issue_type.lower() == "bug":
                return NoteType.FIXED
            else:
                return NoteType.ADDED

        release_notes = my_jira.release_notes.strip()
        try:
            commit_dict = parse_conventional_commit(release_notes)
            if not commit_dict.get("type"):
                commit_dict["type"] = str(_note_type_from_jira())
            if not commit_dict.get("scope"):
                commit_dict["scope"] = str(_note_scope_from_jira())
            commit_dict["jira_key"] = my_jira.key
            return ReleaseNote(**commit_dict)
        except ValueError:
            print(f"Release Note non-conform: {my_jira}")
            # remove any line breaks.
            release_notes = " ".join([line for line in release_notes.split()])
            return ReleaseNote(release_notes, str(_note_type_from_jira()), my_jira.key)

    @staticmethod
    def from_str(release_notes: str):
        commit_dict = parse_conventional_commit(release_notes)
        return ReleaseNote(**commit_dict)


def get_issues_from_jql(jira_client: JIRA, jql: str, use_cache: bool = False) -> list[Issue]:
    if use_cache and JIRA_CACHE.exists():
        with open(JIRA_CACHE, "rb") as f:
            return pickle.load(f)

    issues: list[Issue] = []
    max_results = 50
    start_at = 0
    while True:
        results = jira_client.search_issues(jql, startAt=start_at, maxResults=max_results)
        issues.extend(results)
        if len(results) < max_results:
            break
        start_at += max_results

    if use_cache:
        with open(JIRA_CACHE, "wb") as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(issues, f, pickle.HIGHEST_PROTOCOL)

    return issues


def my_jiras_to_rst(my_jiras: list[MyJira]) -> str:
    ret_rst = ""
    release_notes = [ReleaseNote.from_my_jira(my_jira) for my_jira in my_jiras]
    sorted_notes: list[ReleaseNote] = sorted(release_notes, key=lambda obj: (obj.scope is None, obj.scope))
    release_notes_by_type: dict[str, ReleaseNote] = defaultdict(list)

    for note in sorted_notes:
        note_type = note.type.lower()
        if note_type in ("fix", "fixed"):
            release_notes_by_type[NoteType.FIXED].append(note)
        elif note_type in ("improved", "perf"):
            release_notes_by_type[NoteType.IMPROVED].append(note)
        elif note_type in ("sec"):
            release_notes_by_type[NoteType.SECURITY].append(note)
        elif note_type in ("dep", "deprecated"):
            release_notes_by_type[NoteType.DEPRECATED].append(note)
        elif note_type in ("rem", "removed", "del"):
            release_notes_by_type[NoteType.REMOVED].append(note)
        else:
            release_notes_by_type[NoteType.ADDED].append(note)

    for note_type in NoteType:

        if not release_notes_by_type[note_type]:
            continue
        ret_rst += f"{note_type.title()}\n"
        ret_rst += ("*" * len(note_type)) + "\n"
        for note in release_notes_by_type[note_type]:
            if note.scope:
                ret_rst += f"- {note.scope} - {note.description} [{note.jira_key}]\n"
            else:
                ret_rst += f"- {note.description} [{note.jira_key}]\n"
        ret_rst += "\n\n"
    return ret_rst


def main(jira_server, jira_token_auth, jql_query, update_cache):
    jira_client = JIRA(server=jira_server, token_auth=jira_token_auth, validate=True)
    issues = get_issues_from_jql(jira_client, jql_query, update_cache)

    my_jiras = [MyJira.from_issue(issue) for issue in issues]
    rst = my_jiras_to_rst(my_jiras)
    print(rst)


if __name__ == "__main__":

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Retrieve Jira issues based on a JQL query.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--JIRA_SERVER",
        help="Jira server URL (optional)",
        default=JIRA_SERVER,
    )
    parser.add_argument(
        "--JIRA_USER_TOKEN",
        help="Jira user API token for authentication",
        required=False,
    )
    parser.add_argument("--JQL", help="Jira Query Language (JQL) string", default=DEFAULT_JQL)
    parser.add_argument("--USE_CACHE", help="Use JIRA cache.", default=False)

    args = parser.parse_args()

    jira_server = args.JIRA_SERVER
    jira_token_auth = args.JIRA_USER_TOKEN or os.getenv("JIRA_USER_TOKEN")
    jql_query = args.JQL
    use_cache = args.USE_CACHE

    if not jira_token_auth:
        raise ValueError("JIRA_USER_TOKEN not defined")

    main(jira_server, jira_token_auth, jql_query, use_cache)
