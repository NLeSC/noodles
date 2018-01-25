import pytest
from test.workflows import workflows
from test.backends import backends


def pytest_addoption(parser):
    # parser.addoption("--all", action="store_true",
    #    help="run all combinations")
    parser.addoption("--workflow",
        help="run test only on specified workflow")
    parser.addoption("--backend",
        help="run test only using specified backend")


def pytest_generate_tests(metafunc):
    if 'workflow' in metafunc.fixturenames:
        selection = metafunc.config.getoption('workflow')
        if selection is None:
            metafunc.parametrize(
                "workflow", list(workflows.values()),
                ids=list(workflows.keys()))
        else:
            metafunc.parametrize(
                "workflow", [workflows[selection]],
                ids=[selection])

    if 'backend' in metafunc.fixturenames:
        selection = metafunc.config.getoption('backend')
        if selection is None:
            metafunc.parametrize(
                "backend", list(backends.values()),
                ids=list(backends.keys()))
        else:
            metafunc.parametrize(
                "backend", [backends[selection]],
                ids=[selection])


try:
    import xenon
except ImportError:
    pass
else:
    @pytest.fixture(scope="session")
    def xenon_server(request):
        print("============== Starting Xenon-GRPC server ================")
        m = xenon.init(do_not_exit=True, disable_tls=False, log_level='INFO')
        yield m

        print("============== Closing Xenon-GRPC server =================")
        for scheduler in xenon.Scheduler.list_schedulers():
            jobs = list(scheduler.get_jobs())
            statuses = scheduler.get_job_statuses(jobs)
            for status in statuses:
                if status.running:
                    print("xenon job {} still running, cancelling ... "
                          .format(status.job.id), end='')
                    try:
                        status = scheduler.cancel_job(status.job)
                        if not status.done:
                            scheduler.wait_until_done(status.job)
                    except xenon.XenonException:
                        print("not Ok")
                    else:
                        print("Ok")

        m.__exit__(None, None, None)

    @pytest.fixture
    def local_filesystem(request, xenon_server):
        fs = xenon.FileSystem.create(adaptor='file')
        yield fs
        fs.close()

    @pytest.fixture
    def local_scheduler(request, xenon_server):
        scheduler = xenon.Scheduler.create(adaptor='local')
        yield scheduler
        scheduler.close()
