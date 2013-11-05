import unittest
import pypipe
import os
import subprocess


class Test(unittest.TestCase):

    def setUp(self):
        cur_dir = os.path.dirname(__file__)
        self._data_path = os.path.join(cur_dir, 'test_data')

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

    def testTailCtor(self):
        # test tail with file
        test_file = os.path.join(self._data_path, 'multiline.txt')
        cls_obj = pypipe.Tail(test_file, 3)
        res = []
        for _l in cls_obj:
            res.append(_l)

        self.assertEqual(['555\n', '333\n', '111'], res)


    def testMapCtor(self):
        test_file = os.path.join(self._data_path, 'multiline.txt')
        cls_obj = pypipe.Map(test_file, lambda l: int(l))
        res = []
        for _l in cls_obj:
            res.append(_l)
        
        with open(test_file) as fd:
            expected = [int(l) for l in fd]
            self.assertEqual(expected, res)


    def testHeadCtor(self):
        test_file = os.path.join(self._data_path, 'multiline.txt')
        cls_obj = pypipe.Head(test_file, 3)
        res = []
        for _l in cls_obj:
            res.append(_l)

        self.assertEqual(['123\n', '456\n', '123\n'], res)
        
        
    def testGrepCtor(self):
        test_file = os.path.join(self._data_path, 'multiline.txt')
        cls_obj = pypipe.Grep(test_file, r'222')
        res = []
        for _l in cls_obj:
            res.append(_l)
        
        with open(test_file) as fd:
            expected = [l for l in fd if '222' in l]
            self.assertEqual(expected, res)


    def testFilterCtor(self):
        test_file = os.path.join(self._data_path, 'multiline.txt')
        cls_obj = pypipe.Filter(test_file, lambda l: int(l) % 2 == 0)
        res = []
        for _l in cls_obj:
            res.append(_l)
        
        with open(test_file) as fd:
            expected = [l for l in fd if int(l) % 2 == 0]
            self.assertEqual(expected, res)


    def testShCtor(self):
        # test with None stream arg
        cls_obj = pypipe.Sh(None, 'cat ' + os.path.join(self._data_path, 'input.txt'))
        res = []
        for _l in cls_obj:
            res.append(_l)

        self.assertEqual(['hello'], res)

    def testShGetProcess(self):
        cls_obj = pypipe.Sh(None, 'cat ' + os.path.join(self._data_path, 'input.txt'))
        self.assertIsInstance(cls_obj.get_process(), subprocess.Popen)

    def testShFollowingNonSh(self):
        # test the normal case
        test_file = os.path.join(self._data_path, 'multiline.txt')
        res = []
        for _l in pypipe.Grep(test_file, r'222').sh('head -n 2'):
            res.append(_l)
            
        self.assertEqual(['222\n', '222\n'], res)

    def testColCtor(self):
        test_file = os.path.join(self._data_path, 'multicol.txt')
        cls_obj = pypipe.Col(test_file, 0)
        res = []
        for _l in cls_obj:
            res.append(_l)
        
        self.assertEqual(['123\n', '456\n', 'aaa\n'], res)


    def testStreamList(self):
        test_file = os.path.join(self._data_path, 'multicol.txt')
        cls_obj = pypipe.Col(test_file, 0)
        self.assertEqual(['123\n', '456\n', 'aaa\n'], cls_obj.list())


    def testStreamGetattr(self):
        pass # do special test for Stream.__getattr__


    def testStreamIter(self):
        pass # do special test for Stream.__iter__


    def testStreamLen(self):
        pass # do special test for Stream.__len__



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()