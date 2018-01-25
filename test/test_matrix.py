"""
Test available runners on a variety of workflows.
"""

import pytest


def test_run(workflow, backend):
    if not backend.supports(workflow.requires):
        pytest.skip("Workflow not supported on this backend.")

    if workflow.raises is not None:
        with pytest.raises(workflow.raises):
            backend.run(workflow.make())
    else:
        result = backend.run(workflow.make())
        workflow.check_assertions(result)
