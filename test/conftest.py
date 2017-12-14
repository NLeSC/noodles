import pytest

try:
    import xenon


    @pytest.fixture(scope="session")
    def xenon_server(request):
        print("============== Starting Xenon-GRPC server ================")
        m = xenon.init(do_not_exit=True, disable_tls=False, log_level='INFO')
        yield m
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


except ImportError:
    pass
