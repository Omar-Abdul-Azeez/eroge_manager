from os import walk
from os.path import sep


def walklevel(path, depth=1):
    """It works just like os.walk, but you can pass it a level parameter
       that indicates how deep the recursion will go.
       If depth is 1, the current directory is listed.
       If depth is 0, nothing is returned.
       If depth is -1 (or less than 0), the full depth is walked.
    """
    # If depth is negative, just walk
    # and copy dirs to keep consistent behavior for depth = -1 and depth = inf
    if depth < 0:
        for root, dirs, files in walk(path):
            yield root, dirs[:], files
        return
    elif depth == 0:
        return

    base_depth = path.rstrip(sep).count(sep)
    for root, dirs, files in walk(path):
        yield root, dirs[:], files
        cur_depth = root.count(sep)
        if base_depth + depth <= cur_depth:
            del dirs[:]
