
def deep_map(f, root):
    """Passes all objects in a hierarchy through a function.

    If the function `f` returns either a `list` or a `dict`,
    the values in the return value are recursively passed through
    `f`. This function can be used as an alternative to JSON encoding
    with an object hook. Currently it is very hard to trigger the JSON
    encoder hook on an object that is derived from `list` or `dict`.

    Internally this function works on a stack(like list), so no recursive
    call is being made.

    :param f:
        Function taking an object, returning another representation
        of that object.
    :type f: Callable

    :param root:
        The root object to start with.
    :type root: Any

    :returns: In quasi code: `f(root).map(deep_map(f, -))`
    :rtype: Any"""
    memo = {}

    # stage 1: map all objects
    q = [root]
    while len(q) != 0:
        obj = q.pop()

        if id(obj) not in memo:
            jbo = f(obj)

            if isinstance(jbo, dict):
                q.extend(jbo.values())

            elif isinstance(jbo, list):
                q.extend(jbo)

            else:
                continue

            memo[id(obj)] = jbo


    # stage 2: redirect links to mapped objects
    q = [id(root)]
    while len(q) != 0:
        i = q.pop()

        if i not in memo:
            continue

        if isinstance(memo[i], dict):
            for k, v in memo[i].items():
                if id(v) in memo:
                    memo[i][k] = memo[id(v)]
                    q.append(id(v))

        elif isinstance(memo[i], list):
            for k, v in enumerate(memo[i]):
                if id(v) in memo:
                    memo[i][k] = memo[id(v)]
                    q.append(id(v))

    return memo.get(id(root), root)


