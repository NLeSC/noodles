from nose.tools import raises

from engine.decorator import _pluck_arguments
from lib import *

################################################################################
# Test with simple function
#-------------------------------------------------------------------------------
def f_simple(a, b, c):
    """
    Test function taking three regular arguments, passing.
    """
    pass

def test_pluck_arguments_s1():    
    assert _pluck_arguments(f_simple, [1, 2, 3], {}) == ([1,2,3], None, None)

def test_pluck_arguments_s2():
    assert _pluck_arguments(f_simple, [1], {'c': 3, 'b': 2}) == ([1,2,3], None, None)

@raises(MissingArgument)
def test_pluck_arguments_s_missing():
    assert _pluck_arguments(f_simple, [1, 2], {})
    
@raises(DuplicateArgument)
def test_pluck_arguments_s_duplicate():
    assert _pluck_arguments(f_simple, [1, 2], {'c': 3, 'b': 4})

@raises(SpuriousArgument)
def test_pluck_arguments_s_spurious():
    _pluck_arguments(f_simple, [1, 2, 3, 4], {})

@raises(SpuriousKeywordArgument)
def test_pluck_arguments_s_spurious_keyword():
    _pluck_arguments(f_simple, [1, 2, 3], {'d': 4})

################################################################################
# Test with function having variadic arguments
#-------------------------------------------------------------------------------
def f_variadic(a, b, *c):
    """
    Test function taking two regular arguments and variadic arguments, passing.
    """
    pass
    
def test_pluck_arguments_v1():
    assert _pluck_arguments(f_variadic, [1, 2, 3, 4, 5], {}) \
        == ([1, 2], [3, 4, 5], None)

def test_pluck_arguments_v2():
    assert _pluck_arguments(f_variadic, [1], {'b': 2}) \
        == ([1, 2], None, None)

@raises(MissingArgument)
def test_pluck_arguments_v_missing():
    _pluck_arguments(f_variadic, [1], {})

@raises(DuplicateArgument)
def test_pluck_arguments_v_duplicate():
    assert _pluck_arguments(f_variadic, [1, 2, 3, 4, 5], {'c': 3, 'b': 4})

@raises(SpuriousKeywordArgument)
def test_pluck_arguments_v_spurious_keyword():
    _pluck_arguments(f_variadic, [1, 2, 3], {'d': 4})

################################################################################
# Test with function having variadic, and keyword arguments
#-------------------------------------------------------------------------------
def f_keyword(a, b, *c, **d):
    """
    Test function taking two regular arguments and variadic arguments, passing.
    """
    pass
    
def test_pluck_arguments_k1():
    assert _pluck_arguments(f_keyword, [1, 2, 3, 4, 5], {'d': 42}) \
        == ([1, 2], [3, 4, 5], {'d': 42})

def test_pluck_arguments_k2():
    assert _pluck_arguments(f_keyword, [1], {'b': 2}) \
        == ([1, 2], None, None)

def test_pluck_arguments_k3():
    assert _pluck_arguments(f_keyword, [1], {'b': 2}) \
        == ([1, 2], None, None)

@raises(MissingArgument)
def test_pluck_arguments_k_missing():
    _pluck_arguments(f_keyword, [], {'b': 5})

@raises(DuplicateArgument)
def test_pluck_arguments_k_duplicate():
    assert _pluck_arguments(f_keyword, [1, 2, 3, 4, 5], {'d': 42, 'b': 4})

################################################################################
# Test with function having defaults, variadic, and keyword arguments
#-------------------------------------------------------------------------------
def full_monty(a, b, c = 3, d = 4, *e, **f):
    """
    Test function taking regular, variadic, keyword arguments and having 
    defaults, passing.
    """
    pass
    
def test_pluck_arguments_f1():
    assert _pluck_arguments(full_monty, list(range(1,10)), {}) \
        == ([1, 2, 3, 4], [5, 6, 7, 8, 9], None)

def test_pluck_arguments_f2():
    assert _pluck_arguments(full_monty, [1, 2], {}) \
        == ([1, 2, 3, 4], None, None)

def test_pluck_arguments_f3():
    assert _pluck_arguments(full_monty, [1], {'b': 5, 'd': 7, 'g': 11}) \
        == ([1, 5, 3, 7], None, {'g': 11})


