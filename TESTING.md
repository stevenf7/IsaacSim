# Omniverse Isaac Sim Testing
This document will cover how to run and write tests for this repository

## Running Tests
These are the types of tests that you can run:
### Startup Tests
These tests make sure that kit starts up and runs with the extensions specified in the associated config files. Any experience (except for the unit test experience)

These tests are run using the following script:

``./tools/ci/testing/test-linux-x86_64-release-startup-tests-ubuntu18/step.sh``

### Unit Tests
This set of tests run per extension and are user defined. Any extension specified in the config file will be loaded and its tests executed.

See the 
``source/experiences`` folder for all test app configuration files

## Writing Unit Tests
Writing unit tests involves three steps
1. Creating a python file with tests in the source folder for that extension
2. Loading the python test file in the main extension
3. Making sure the extension being tested is in the test app configuration 

### 1. Creating a python file with tests

Every set of extension tests have a similar directory structure:

- extension_name
    - python
        - scripts
            - extension.py
            - tests
                - test_extension.py

``test_extension.py`` contains the following structure
```
import omni.kit.test

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.foo import _foo

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestFoo(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_something(self):
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_something_else(self):
        pass
```

### 2. Loading the test into the extension

``extension.py`` generally has the following format, the important part is to import any tests from that extensions scripts/tests folder. 

```
import omni.ext
from .. import _extension

# Any unit tests for the extension should be imported here
from .tests.test_extension import *

class Extension(omni.ext.IExt):
    def on_startup(self):
        ...

    def on_shutdown(self):
        ...

```

Tests can be structured into multiple python files as it makes sense. 
For an example of how to set up a test see the motion_planning extension

### 3. Add test to app config json

modify ``source/experiences/test-isaac-sim.json`` and add the extension to the list of extensions loaded on startup, the test will automatically get picked up by the test-runner extension and run. 