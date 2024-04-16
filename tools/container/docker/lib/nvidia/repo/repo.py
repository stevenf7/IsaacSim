import os 
import sys
from pprint import pprint 

from nvidia.die import die

import logging 


################################################################################
################################################################################
################################################################################

VERSION_FILE = "VERSION.md"

def find_repo_root(p, prefix = ''):
  logging.info(f"{prefix}> {p}")
  if(p == '/'):
    die("We're at `/`, can't proceed")

  v_f = os.path.join(p, VERSION_FILE) 
  if(os.path.isfile(v_f)):
     logging.info(f"{prefix}> found {v_f}, returning!")
     return(p)
  else:
    p = os.path.dirname(p)
    return(find_repo_root(p, prefix=f"{prefix}  "))

################################################################################
################################################################################
