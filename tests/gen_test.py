import sys
import types


_UT_TEMPLATE = '''
import unittest
import %s


class Test(unittest.TestCase):
%s 
    def tearDown(self):
        pass
    
%s

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
'''

_UT_SETUP_METHOD_TEMPLATE = '''
    def setUp(self):
        %s
'''

_UT_METHOD_TEMPLATE = '''
    def test%s(self):
        %s
'''

def get_default_ut_setup_method():
    return _UT_SETUP_METHOD_TEMPLATE % 'pass'

def get_test_method_name(func_name):
    return ''.join([elem.capitalize() for elem in func_name.split('_')])

def gen_test_for_func(func):
    code_obj = func.func_code
    argcount = code_obj.co_argcount
    varnames = code_obj.co_varnames
    func_args = ', '.join(["'%s'" % var
                           for var in varnames[0:argcount]])
    mod_name = func.func_globals['__name__']
    func_calling = '%s.%s(%s)' % (mod_name, func.func_name, func_args)
    self_arg = 'self'
    assert_func = '%s.assertTrue(%s)' % (self_arg, func_calling)
    return _UT_METHOD_TEMPLATE % (get_test_method_name(func.func_name), assert_func)

def gen_test_for_method(cls_name, method_name, method):
    code_obj = method.func_code
    argcount = code_obj.co_argcount
    varnames = code_obj.co_varnames
    method_args = ', '.join(["'%s'" % var
                             for var in varnames[1:argcount]])
    func_calling = '%s(%s)' % (method_name, method_args)
    obj_arg = 'self.%s' % cls_name
    assert_func = 'self.assertTrue(%s.%s)' % (obj_arg, func_calling)
    method_name = cls_name.capitalize() + method_name.capitalize()
    return _UT_METHOD_TEMPLATE % (get_test_method_name(method_name), assert_func)

def gen_test_for_ctor(cls):
    method_name = cls.__name__.capitalize() + 'Ctor'
    test_code_tpl = \
'''cls_obj = %s(%s)
        self.assertTrue(cls_obj)'''
    
    if '__init__' in cls.__dict__:
        func_code = cls.__dict__['__init__'].func_code
        argcount = func_code.co_argcount
        varnames = func_code.co_varnames
        method_args = ', '.join(["'%s'" % var
                                 for var in varnames[1:argcount]])
    else:
        method_args = ''
    
    ctor_call = '%s.%s' % (cls.__module__, cls.__name__)
    test_code = test_code_tpl % (ctor_call, method_args)
    return _UT_METHOD_TEMPLATE % (method_name, test_code)

def gen_test_for_special_method(cls_name, method_name, _):
    test_code = 'pass # do special test for %s.%s' % (cls_name, method_name)
    test_method_name = cls_name.capitalize() + method_name[2:-2].capitalize()
    return _UT_METHOD_TEMPLATE % (test_method_name, test_code)

def gen_tests_for_class(cls):
    test_methods = [gen_test_for_ctor(cls)]
    cls_name = cls.__name__
    for attr_name, v in cls.__dict__.iteritems():
        if not attr_name.startswith('_') and isinstance(v, types.FunctionType):
            test_methods.append(gen_test_for_method(cls_name, attr_name, v))
        elif attr_name.startswith('__') and attr_name.endswith('__') and \
            isinstance(v, types.FunctionType):
            # builtin methods
            if attr_name != '__init__': # skip constructor
                test_methods.append(gen_test_for_special_method(cls_name, attr_name, v))
    
    return '\n'.join(test_methods)

def gen_test(target):
    if isinstance(target, types.FunctionType):
        return gen_test_for_func(target)
    elif isinstance(target, type):
        # assume it's a class
        return gen_tests_for_class(target)
    else:
        raise ValueError, 'not supported type'

if __name__ == '__main__':
    mod_name, obj_name = sys.argv[1:]
    
    mod_nane = mod_name.split()[0]
    mod = __import__(mod_name)
    
    if obj_name == '@all': # special target meaning that tests everything.
        test_methods = []
        for k, v in mod.__dict__.iteritems():
            if not k.startswith('_'):
                try:
                    test_methods.append(gen_test(v))
                except ValueError:
                    continue
        
        print _UT_TEMPLATE % (mod_name, get_default_ut_setup_method(),
                              '\n'.join(test_methods))
    else:
        try:
            target = mod.__dict__[obj_name]
            print _UT_TEMPLATE % (mod_name, get_default_ut_setup_method(),
                                  gen_test(target))
        except ValueError, e:
            print e
            sys.exit(1)
