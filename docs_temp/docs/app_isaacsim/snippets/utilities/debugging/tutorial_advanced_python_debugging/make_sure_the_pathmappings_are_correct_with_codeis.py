{
    "name": "Python Debugger: Docker Attach",
    "type": "debugpy",
    "request": "attach",
    "connect": {"host": "localhost", "port": 5678},
    "pathMappings": [{"localRoot": "${workspaceFolder}/_build/linux-x86_64/release", "remoteRoot": "/isaac-sim"}],
},
