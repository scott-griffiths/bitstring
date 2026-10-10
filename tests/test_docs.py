import doctest

import pytest

import bitstring


@pytest.mark.skipif(bitstring.__doc__ is None, reason="docstrings are stripped by -OO")
def test_module_docstring_examples():
    # help(bitstring) shows the module docstring, so its examples need to stay true.
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS, verbose=False)
    test = doctest.DocTestParser().get_doctest(bitstring.__doc__, {}, "bitstring", None, 0)
    assert test.examples, "the module docstring has no examples"
    runner.run(test)
    assert runner.failures == 0, (
        f"{runner.failures} of {runner.tries} examples in the module docstring "
        f"failed (the mismatches are printed above)"
    )
