#!/usr/bin/python3.6

################################################################################
## Libs
################################################################################

import http.server
import socketserver

import random
import cowsay 

from pprint import pprint

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))

import argparse
import logging

import signal

################################################################################
## Globals
################################################################################

description = """
Demo Python script for Docker.
Creates a simple HTTP server.
"""

args = None

class settings:
  port = 8888

################################################################################
## Init
################################################################################

def init():
  signal.signal(signal.SIGINT, shutdown_func)
  signal.signal(signal.SIGTERM, shutdown_func)

  parse_args()

  if(args.log_dir):
    if(not os.path.isdir(args.log_dir)):
      os.makedirs(args.log_dir)

    log_format = "[%(asctime)s][OV] %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO)
    logging.info("foo")
    f_h = logging.FileHandler(os.path.join(args.log_dir, "log.log"))
    f_h.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(f_h)

################################################################################
## Main
################################################################################

def main():
  src_dir = args.dir[0]

  sample_env = os.getenv("OV_SAMPLE_ENV_VAR", None)
  if(sample_env):
    env_message = f"Sample env var is `{sample_env}`"
  else:
    env_message = f"Sample env var not set"

  logging.info("Okay, this server doesn't really log anything to a file")
  logging.info("But I have to pretend I do for the sake of the demo")
  logging.info("So, here:")
  logging.info("Server started up!")

  logging.info(env_message)

  os.chdir(src_dir)
  Handler = http.server.SimpleHTTPRequestHandler
  with socketserver.TCPServer(("", settings.port), Handler) as httpd:
    random.choice(cowsay.chars)(f"{env_message}\n" + 
                                f"serving directory `{src_dir}`\n" + 
                                f"port: `{settings.port}`")
    httpd.serve_forever()

    
################################################################################
## Functions
################################################################################

def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("dir", metavar="dir", nargs=1,
                         default=None,
                         help="Directory to serve from"
                        )

  argparser.add_argument("-l", "--log-dir", metavar="dir", 
                         dest="log_dir", 
                         required=0,
                         default=None,
                         help="Directory to put logs into"
                        )

  global args
  args = argparser.parse_args()

def shutdown_func(sig, frame): 
  logging.info(f"Signal {sig}, shutting down")
  sys.exit(0)

################################################################################
## Execute
################################################################################

init()
main()


