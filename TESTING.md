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

These tests are run using the following script:
``./tools/ci/testing/test-linux-x86_64-release/step.sh``

### Python Sample Tests
These are tests for the source/python_samples. Search for an example like "python_sample_test("tests-python.isaac_sdk.pose_estimation", "isaac_sdk/pose_estimation.py", "--test")."

It'll generate tests-python.isaac_sdk.pose_estimation.sh in the _build/linux-x86_64/release folder that you can run.

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
class TestFoo(omni.kit.test.AsyncTestCase):
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
You can add your extension tests in its __init__.py 

Tests can be structured into multiple python files as it makes sense. 
For an example of how to set up a test see the motion_planning extension

### 3. Running your tests
Team City will pick up all these tests.
To run your tests locally in Kit, you can run those test-*.sh in the release folder. Or use the Kit's UI Window / Test Runner and search for your tests.