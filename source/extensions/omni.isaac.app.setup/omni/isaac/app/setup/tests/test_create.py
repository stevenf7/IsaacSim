import omni.kit.test


class Test(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def test_create_basic(self):
        self.assertEqual(1, 1)
