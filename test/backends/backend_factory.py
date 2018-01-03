class backend_factory:
    def __init__(self, runner, *args, **kwargs):
        self.runner = runner
        self.args = args
        self.kwargs = kwargs

    def run(self, workflow):
        return self.runner(workflow, *self.args, **self.kwargs)
