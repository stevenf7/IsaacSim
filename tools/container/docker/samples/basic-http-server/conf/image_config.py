#!/usr/bin/env python3

# Docker image name basically
service_name = "sample-http-server"

# Root - relative to config - for files' spec
root = '../'


# Source files to set up in the build directory 
files = [
          {
            'source': '.', # Source *subdir* 
            'dest'  : '',  # Destination *subdir* (can be empty)

            'files' :      # Source files to copy, relative to source
                           # subdir
                      [
                        'server.py',
                        'requirements.txt',
                      ]
          },
          {
            'source': 'html/',

            'dest'  : 'html/',  # Destination *subdir* (can be empty)

            'files' :           # Source files to copy, relative to source
                                # subdir
                      [
                        '*',
                      ]
          }
        ]

ignore = [ 'foo/*', 
           'bar' ]

# Should return a string containing dockerfile.
def dockerfile(release=None, family=None, build=None):
  dockerfile =  f"""
FROM python:3.6-alpine

WORKDIR /sample/

RUN mkdir /sample/log

ADD server.py .
ADD requirements.txt .
ADD html/ html/

RUN pip install -r requirements.txt

LABEL com.nvidia.omniverse.service="{service_name}"

LABEL com.nvidia.omniverse.build.release="{release}"
LABEL com.nvidia.omniverse.build.family="{family}"
LABEL com.nvidia.omniverse.build.build="{build}"

EXPOSE 8888

CMD [ "python3.6", "./server.py", "-l", "log/", "html/"]
  """
  return dockerfile



