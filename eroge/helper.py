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


def ask(msg, choices, index=False, show=False, default=None, limit=0, none=False):
    while True:
        print(msg)
        if show:
            for i in range(len(choices)):
                if limit != 0 and i != 0 and i % limit == 0:
                    ans = input('>')
                    if ans != '':
                        if ans in choices:
                            if index:
                                return choices.index(ans)
                            else:
                                return ans
                        ans = int(ans) - 1
                        if -1 < ans < i:
                            if index:
                                return ans
                            else:
                                return choices[ans]
                    print(msg)
                print(f'{i + 1})  {choices[i]}')
            if none:
                print(f'{i + 2})  None')
        ans = input('>')
        if ans == '' and show:
            return default
        if ans in choices:
            if index:
                return choices.index(ans)
            else:
                return ans

        if show:
            ans = int(ans) - 1
            if ans == len(choices) and none:
                return None
            elif -1 < ans < len(choices):
                if index:
                    return ans
                else:
                    return choices[ans]