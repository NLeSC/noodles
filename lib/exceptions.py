
def _ordinal(n):
    """
    Ugly hack to get ordinal number. Is there an internationalized solution
    to this?
    """
    return "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

class MissingArgument(Exception):
    def __init__(self, func_name, pos, arg_name, doc):
        self.msg = "Missing {rank} argument '{arg}'"           \
                   " in scheduling function call to '{func}'."   \
            .format(rank = _ordinal(pos), arg = arg_name, func = func_name) 
        self.doc = doc if doc else "This function is not documented"
        
    def __str__(self):
        return self.msg + "\n" + self.doc

class DuplicateArgument(Exception):
    def __init__(self, func_name, pos, arg_name, doc):
        self.msg = "Duplicate argument '{arg}'; already given as {rank}" \
                   " argument in call to '{func}'."                        \
            .format(arg = arg_name, rank = _ordinal(pos), func = func_name)
        self.doc = doc if doc else "This function is not documented"
        
    def __str__(self):
        return self.msg + "\n" + self.doc
        
class SpuriousArgument(Exception):
    def __init__(self, func_name, nargs, ngiven, doc):
        self.msg = "Too many arguments; '{func}' takes {nargs} regular" \
                   " arguments and does not take variadic arguments;" \
                   " {ngiven} arguments given."                       \
            .format(func = func_name, nargs = nargs, ngiven = ngiven)
        self.doc = doc if doc else "This function is not documented"
                
    def __str__(self):
        return self.msg + "\n" + self.doc

class SpuriousKeywordArgument(Exception):
    def __init__(self, func_name, doc):
        self.msg = "Function '{func}' does not take keyword arguments." \
            .format(func = func_name)
        self.doc = doc if doc else "This function is not documented"

    def __str__(self):
        return self.msg + "\n" + self.doc
         
