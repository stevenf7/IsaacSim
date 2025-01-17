# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import re
from typing import Optional, Tuple

import carb


class SemanticVersion:
    """
    A semver compatible version class: https://semver.org.
    """

    __slots__ = ("major", "minor", "patch", "prerelease", "build")

    #: Regex to parse semver from string
    # Taken from original https://regex101.com/r/Ly7O1x/3/
    _REGEX = re.compile(
        r"""
            ^
            (?P<major>0|[1-9]\d*)
            (?:
                \.
                (?P<minor>0|[1-9]\d*)
                (?:
                    \.
                    (?P<patch>0|[1-9]\d*)
                )
            )
            (?:-(?P<prerelease>
                (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
                (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
            ))?
            (?:\+(?P<build>
                [0-9a-zA-Z-]+
                (?:\.[0-9a-zA-Z-]+)*
            ))?
            $
        """,
        re.VERBOSE,
    )

    def __init__(
        self,
        major: str,
        minor: str,
        patch: str,
        prerelease: Optional[str],
        build: Optional[str],
    ):
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)
        self.prerelease = prerelease
        self.build = build

    def to_tuple(self) -> Tuple[int, int, int, Optional[str], Optional[str]]:
        """
        Convert the SemanticVersion object to a tuple.
        """
        return (self.major, self.minor, self.patch, self.prerelease, self.build)

    def compare(self, other: "SemanticVersion") -> int:
        """
        Compare self with other.
        """
        v1 = self.to_tuple()[:3]
        v2 = other.to_tuple()[:3]
        x = _cmp(v1, v2)
        if x:
            return x

        rc1, rc2 = self.prerelease, other.prerelease
        rccmp = _cmp_prerelease(rc1, rc2)

        if not rccmp:
            return 0
        if not rc1:
            return 1
        elif not rc2:
            return -1

        return rccmp

    def __eq__(self, other: "SemanticVersion") -> bool:
        return self.compare(other) == 0

    def __ne__(self, other: "SemanticVersion") -> bool:
        return self.compare(other) != 0

    def __lt__(self, other: "SemanticVersion") -> bool:
        return self.compare(other) < 0

    def __le__(self, other: "SemanticVersion") -> bool:
        return self.compare(other) <= 0

    def __gt__(self, other: "SemanticVersion") -> bool:
        return self.compare(other) > 0

    def __ge__(self, other: "SemanticVersion") -> bool:
        return self.compare(other) >= 0

    def __str__(self) -> str:
        version = "%d.%d.%d" % (self.major, self.minor, self.patch)
        if self.prerelease:
            version += "-%s" % self.prerelease
        if self.build:
            version += "+%s" % self.build
        return version

    @staticmethod
    def parse(version: str) -> "SemanticVersion":
        """
        Parse version string to a Version.
        """
        carb.log_info(f"parsing {version}")
        match = SemanticVersion._REGEX.match(version)
        if match is None:
            raise ValueError(f"{version} is not valid SemVer string")

        return SemanticVersion(**match.groupdict())


def _cmp(a, b):
    return (a > b) - (a < b)


def _cmp_prerelease(a, b):
    def cmp_prerelease_part(a, b):
        if isinstance(a, int) and isinstance(b, int):
            return _cmp(a, b)
        elif isinstance(a, int):
            return -1
        elif isinstance(b, int):
            return 1
        else:
            return _cmp(a, b)

    a, b = a or "", b or ""
    a_parts = [int(x) if re.match(r"^\d+$", x) else x for x in a.split(".")]
    b_parts = [int(x) if re.match(r"^\d+$", x) else x for x in b.split(".")]
    for sub_a, sub_b in zip(a_parts, b_parts):
        cmp_result = cmp_prerelease_part(sub_a, sub_b)
        if cmp_result != 0:
            return cmp_result
    else:
        return _cmp(len(a), len(b))
