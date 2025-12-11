#!/usr/bin/env python3
"""
Test file to demonstrate code quality checks
This file has some formatting issues to test the pre-commit hook
"""

import os
from os import path


def bad_function(param1, param2, param3):
    """A function with formatting issues"""
    x = param1 + param2
    y = x * param3
    # TODO: fix this later
    print("Debug info:", x, y)
    return y


def another_bad_function():
    """Function with proper formatting."""
    return path.join(os.getcwd(), "test")


# Long function name broken into multiple lines to respect line length limit
def very_long_function_name_that_exceeds_reasonable_limits(
    parameter_one, parameter_two, parameter_three, parameter_four, parameter_five
):
    """
    Function with a very long name.

    Args:
        parameter_one: First parameter
        parameter_two: Second parameter
        parameter_three: Third parameter
        parameter_four: Fourth parameter
        parameter_five: Fifth parameter

    Returns:
        Sum of all parameters
    """
    return parameter_one + parameter_two + parameter_three + parameter_four + parameter_five
