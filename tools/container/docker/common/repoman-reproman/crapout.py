#!/usr/bin/python3.6 

import sys
import os 
import importlib

from pprint import pprint

bin_path = os.path.dirname(os.path.realpath(sys.argv[0]))

# Bootstrap Repoman 
sys.path.append(os.path.join(bin_path, 'repoman'))
import repoman 
repoman.HOST_DEPS_PATH = os.path.join(bin_path, 'repoman-dependencies')
repoman.bootstrap()

# Call sys.path.append() prior to importing omni.repo.man, and 
# everything will work 
#sys.path.append(f"{bin_path}/packman-dependencies/ovc/python") 

import omni.repo.man
#sys.meta_path = []
#pprint(sys.meta_path)
#sys.exit()
sys.path.append(f"{bin_path}/packman-dependencies/ovc/python") 
#importlib.invalidate_caches()
importlib.reload(sys.modules["omni"])


import omni.aioconnection
pprint(omni.aioconnection)

