import os
from pathlib import Path

import omni.repo.ci

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_ROOT = REPO_ROOT / "_build" / "docs"

if not os.path.exists(DOCS_ROOT):
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "docs", "--warn-as-error=0"])
omni.repo.ci.launch(["${root}/repo${shell_ext}", "docs", "--stage", "sphinx"])
