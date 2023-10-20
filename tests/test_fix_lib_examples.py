from upgraider.fix_lib_examples import _fix_imports

def test_basic_fix_imports():
    old_code = """
import pandas

idx = pandas.Index([0,'1',3, 'fooo'])
if idx.is_mixed():
    print('mixed type')
    """

    new_code = """
import pandas.api.types as pdtypes

idx = pandas.Index([0,'1',3, 'fooo'])
if pdtypes.is_any_real_numeric_dtype(idx):
    print('mixed type')
    """

    expected_code = "import pandas\n" + new_code

    assert _fix_imports(old_code, new_code) == expected_code

def test_module_fix_imports():
    old_code = """
from pandas import Index
from modulex import y as z

print("hello")
    """

    new_code = """
import pandas.api.types as pdtypes

print("hello there")
    """

    # because we always add imports to the top of the file, they will be added in reverse order
    # so just make sure the missing imports are there
    fixed_code = _fix_imports(old_code, new_code)
    assert "from modulex import y as z" in fixed_code
    assert "from pandas import Index" in fixed_code
