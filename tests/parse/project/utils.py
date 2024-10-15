import os


def relative(loc):
    """
    Returns the absolute path to the given location relative to this file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, loc)
