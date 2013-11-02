import unittest
import pypipe
import os


class Test(unittest.TestCase):


    def setUp(self):
        self._data_path = os.path.join(os.getcwd(), 'test_data')


    def tearDown(self):
        pass


    def testStreamCtorWithNone(self):
        stream = pypipe.Stream(None)
        self.assertIs(stream._stream, None)
        self.assertTrue(stream._stream_classes)
        self.assertIn('Stream', stream._stream_classes)
        
    def testStreamCtorWithFile(self):
        stream = pypipe.Stream(os.path.join(self._data_path, 'input.txt'))
        self.assertIsInstance(stream._stream, file)
        self.assertTrue(stream._stream_classes)
        self.assertIn('Stream', stream._stream_classes)
    
    def testSh(self):
        sh_stream = pypipe.sh('cat ' + os.path.join(self._data_path, 'input.txt'))
        self.assertEqual(['hello'], sh_stream.list())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()