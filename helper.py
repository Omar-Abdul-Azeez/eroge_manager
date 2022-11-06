def walklevel(path, depth=1):
    """It works just like os.walk, but you can pass it a level parameter
           that indicates how deep the recursion will go.
           If depth is 1, the current directory is listed.
           If depth is 0, nothing is returned.
           If depth is -1 (or less than 0), the full depth is walked.
        """
    from os.path import sep
    from os import walk
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


def ask(msg, choices=None, show=False, none=False):
    while True:
        print(msg)
        if choices is not None:
            if show:
                if none:
                    print('1)  None')
                for i in range(len(choices)):
                    print(f'{i + (2 if none else 1)})  {choices[i]}')
            ans = input('>')

            if ans in choices:
                return ans

            if show:
                ans = int(ans) - (2 if none else 1)
                if ans == -1:
                    return None
                elif -1 < len(choices):
                    return choices[ans]

        return input('>')
