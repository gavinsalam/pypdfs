""" module cmdline.py

simple command-line access, following the C++ interface;

it could probably be made more efficient with a dictionary, but
that will come later.
"""
from builtins import range

from sys import argv
import copy

# array that initially contains the command line arguments
# but as these are accessed, each entry is set to ""
#_argv_unused = argv.copy()
_argv_unused = copy.copy(argv)

def _error(msg):
    "gives an error and exits"
    raise NameError(msg)

def value(opt, default = None, return_type = None):
    """
    return the value corresponding to option opt;
    if opt is absent and a default was supplied, return the default
    otherwise raise an error.

    If default is present, then the return value is of the same type;
    otherwise the return value is a string

    The return type can be overriden with the return_type argument
    """
    i = index(opt)
    deftype = str
    if (default    != None):  deftype = type(default)
    if (return_type != None): deftype = return_type

    if (i > 0 and len(argv) > i+1): 
        _argv_unused[i+1] = ""
        if (deftype == bool):
            return deftype(int(argv[i+1]))
        else:
            return deftype(argv[i+1])
    elif (default != None):         return default
    else: _error("ERROR: could not find option "+opt)

def present(opt):
    "returns true if the option is present"
    i = index(opt)
    return (i>0)

def cmdline():
    "returns the full command line"
    # there must be a better way of doing it though...
    result = ""
    for i in range(len(argv)):
        result += argv[i]
        if (i+1 != len(argv)): result += " "
    return result
    
def index(opt):
    "return the index of the option (if present), otherwise -1" 
    for i in range(len(argv)):
        if (argv[i] == opt): 
            _argv_unused[i] = ""
            return i
    return -1

def assert_all_options_used():
    "raises an exception if there are unused options / arguments"
    unused = ""
    for i in range(1, len(argv)):
        if (_argv_unused[i] != ""): unused += " "+_argv_unused[i]

    if (unused != ""): _error("ERROR, unused options:"+unused)
