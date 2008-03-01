import os,inspect

from doit.loader import Loader

class TestLoader():
    def setUp(self):
        # this test can be executed from any path
        self.fileName = os.path.abspath(__file__+"/../sample.py")

    def testImport(self):
        loaded = Loader(self.fileName)
        assert inspect.ismodule(loaded.module)

    def testGetTaskGenerators(self):
        loaded = Loader(self.fileName)
        funcNames =  [f.name for f in loaded.getTaskGenerators()]
        expected = ["nose","checker"]
        assert expected == funcNames

    def testRelativeImport(self):
        # test relative import but test should still work from any path
        # so change cwd.
        os.chdir(os.path.abspath(__file__+"/../.."))
        self.fileName = "tests/sample.py"
        self.testImport()


