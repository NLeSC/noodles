from noodles.lib import decorator


@decorator
class workflow_factory:
    instances = []

    def __init__(self, f, result=None, assertions=None, raises=None,
                 requires=None, python_version=None):
        self.instances.append(self)
        self.assertions = assertions
        self.requires = requires
        self.result = result
        self.raises = raises
        self.python_version = python_version
        self.f = f

    def make(self):
        return self.f()

    def check_assertions(self, result):
        if self.result is not None:
            assert result == self.result

        if self.assertions is not None:
            for assertion in self.assertions:
                assert assertion(result)
