import logging 
import sys

from pprint import pprint

class settings:
  log = 0
  stderr = 1

def die(*args):
  message = " ".join(args)
 
  if(settings.log):
    logging.error(message)
  if(settings.stderr):
    sys.stderr.write(message)
    sys.stderr.write("\n")
    sys.stderr.flush()

  sys.exit(1)

def log_instead_of_stderr():
  settings.log = 1
  settings.stderr = 0
