from engine import schedule, _pluck_arguments, run, Workflow

def schedule_class(cls):
    class Wrapped(Worflow):
        def __init__(self, *args, **kwargs):
            self.obj = cls.__new__(cls)
            
            regular, variadic, keywords = _pluck_arguments(
                cls.__init__, (self,) + args, kwargs)
            
            self = merge_workflow(cls.__init__, regular, variadic, keyword)
            
            

@schedule_class
class SomeDataObject:
    """
        Class documentation.
    """
    def __init__(self, a):
        """
            Constructor Documentation.
        """
        self.a = a
    
    def do_something_hard(self):
        print(a*a)
        
A = SomeDataObject(6)
v = run(A)
v.do_something_hard()

