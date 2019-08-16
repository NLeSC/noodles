"""
Test available runners on a variety of workflows.
"""

import pytest
import sys


def test_run(workflow, backend):
    if not backend.supports(workflow.requires):
        pytest.skip("Workflow not supported on this backend.")

    if workflow.python_version is not None and \
            not sys.version_info >= workflow.python_version:
        required = ".".join(map(str, workflow.python_version))
        running = ".".join(map(str, sys.version_info[0:3]))
        pytest.skip("Workflow requires Python >= {}, running Python {}."
                    .format(required, running))

    if workflow.raises is not None:
        with pytest.raises(workflow.raises):
            backend.run(workflow.make())
    else:
        result = backend.run(workflow.make())
        workflow.check_assertions(result)
