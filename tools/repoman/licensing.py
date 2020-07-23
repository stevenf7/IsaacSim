import os
import sys
import logging
import argparse
import atexit

logger = logging.getLogger(os.path.basename(__file__))


def main():
    import repoman

    repoman.bootstrap()
    import omni.repo.man
    import omni.repo.man.teamcity
    import omni.repo.licensing

    # setting up the teamcity blocks
    omni.repo.man.teamcity.open_teamcity_block("Licensing", f"Kit {os.getenv('BUILD_NUMBER', '0')}")
    atexit.register(omni.repo.man.teamcity.close_teamcity_block, "Licensing")

    omni.repo.licensing.main()


if __name__ == "__main__":
    main()
