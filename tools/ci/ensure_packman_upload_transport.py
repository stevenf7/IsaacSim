# Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""Ensure the Kit-bundled packman config has a cloudfront upload transport.

The publish-extensions pipeline runs ``omni.kit.registry.nucleus`` which shells
out to the Kit-bundled packman binary (e.g.
``_build/<plat>/<cfg>/kit/dev/tools/packman/packman``) to push extension
archives to the ``cloudfront`` remote. Some published kit-kernel builds ship a
``config.packman.xml`` with the ``cloudfront`` remote declared for downloads
only, which makes ``packman push`` fail with:

    Remote 'packman:cloudfront' doesn't have a transport configured for
    'upload' action

This script injects the missing ``<transport actions="upload" .../>`` element
under the ``cloudfront`` remote in place, preserving every other remote and
transport the Kit-bundled config already declares (e.g. ``urm``). It's a no-op
when the upload transport is already present, so it can stay wired into CI
even after the upstream Kit fix lands.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

UPLOAD_TRANSPORT = {
    "actions": "upload",
    "protocol": "s3",
    "packageLocation": "packages-for-cloudfront",
}


def ensure_upload_transport(config_path: Path) -> int:
    """Add the cloudfront upload transport to ``config_path`` if it's missing.

    Returns 0 on success (including no-op), 1 if the cloudfront remote is
    absent (treated as a warning, not a hard error, so CI can still proceed
    and surface the underlying problem in the publish step itself).
    """
    if not config_path.is_file():
        print(
            f"ensure_packman_upload_transport: {config_path} does not exist; skipping",
            file=sys.stderr,
        )
        return 1

    tree = ET.parse(config_path)
    root = tree.getroot()
    cloudfront = root.find("./remote2[@name='cloudfront']")
    if cloudfront is None:
        print(
            f"ensure_packman_upload_transport: no cloudfront remote in {config_path}; skipping",
            file=sys.stderr,
        )
        return 1

    if cloudfront.find("./transport[@actions='upload']") is not None:
        print(
            f"ensure_packman_upload_transport: upload transport already present in {config_path}; nothing to do"
        )
        return 0

    ET.SubElement(cloudfront, "transport", UPLOAD_TRANSPORT)
    tree.write(config_path, xml_declaration=False, encoding="utf-8")
    print(f"ensure_packman_upload_transport: added cloudfront upload transport to {config_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "config_path",
        type=Path,
        help="Path to the Kit-bundled config.packman.xml to patch in place.",
    )
    args = parser.parse_args(argv)
    return ensure_upload_transport(args.config_path)


if __name__ == "__main__":
    sys.exit(main())
