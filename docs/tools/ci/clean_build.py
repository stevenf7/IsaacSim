import os
import sys
from pathlib import Path

import omni.repo.ci

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_ROOT = REPO_ROOT / "_build" / "docs"

if os.path.exists(DOCS_ROOT):
    print("Starting clean build. Will erase _build/docs. Y/N?")
    _input = input()
    if _input not in ["y", "Y", "yes", "Yes", "YES"]:
        sys.exit()

omni.repo.ci.launch(["${root}/repo${shell_ext}", "docs", "--warn-as-error=0"])
omni.repo.ci.launch(["${root}/repo${shell_ext}", "docs", "--stage", "sphinx"])
