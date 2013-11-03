import sys
import types


_UT_TEMPLATE = '''
import unittest


class Test(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
    
%s

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
'''

_UT_METHOD_TEMPLATE = '''
    def test%s(self):
        %s
'''

def gen_tests_for_func(func):
    code_obj = func.func_code
    func_args = ', '.join(['arg%d' % i
                           for i in xrange(code_obj.co_argcount)])
    func_calling = '%s(%s)' % (func.func_name, func_args)
    self_arg = 'self'
    assert_func = '%s.assertTrue(%s)' % (self_arg, func_calling)
    return _UT_METHOD_TEMPLATE % (func.func_name, assert_func)


def gen_tests_for_class(cls):
    pass

if __name__ == '__main__':
    mod_name, obj_name = sys.argv[1:]
    
    mod = __import__(mod_name)
    
    target = mod.__dict__[obj_name]
    
    if isinstance(target, types.FunctionType):
        print _UT_TEMPLATE % gen_tests_for_func(target)
    elif isinstance(target, type):
        # assume it's a class
        gen_tests_for_class(target)
    else:
        print 'Not support'
        sys.exit(1)
        

