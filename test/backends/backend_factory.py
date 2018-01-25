class backend_factory:
    def __init__(self, runner, supports=None, *args, **kwargs):
        self.runner = runner
        self._supports = supports or []
        self.args = args
        self.kwargs = kwargs

    def supports(self, requires):
        if requires is None:
            return True

        return all((requirement in self._supports)
                   for requirement in requires)

    def run(self, workflow):
        return self.runner(workflow, *self.args, **self.kwargs)
