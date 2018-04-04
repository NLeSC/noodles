import uuid
import xenon

from ..remote.worker_config import WorkerConfig


class XenonJobConfig(WorkerConfig):
    def __init__(
            self, *, queue_name=None, environment=None, options=None,
            time_out=1000, scheduler_arguments=None, **kwargs):
        super(XenonJobConfig, self).__init__(**kwargs)
        self.time_out = time_out

        executable, arguments = self.command_line()
        self.xenon_job_description = xenon.JobDescription(
            executable=str(executable),
            arguments=arguments,
            working_directory=str(self.working_dir),
            queue_name=queue_name,
            environment=environment,
            scheduler_arguments=scheduler_arguments,
            options=options)


class Machine(object):
    """Configuration to the Xenon library.

    Xenon is a Java library that offers a uniform interface to execute jobs.
    These jobs may be run locally, over ssh ar against a queue manager like
    SLURM.

    [Documentation to PyXenon can be found online](http://pyxenon.rtfd.io/)

    :param name:
        The quasi human readable name to give to this Xenon instance.
        This defaults to a generated UUID.

    :param jobs_scheme:
        The scheme by which to schedule jobs. Should be one of 'local', 'ssh',
        'slurm' etc. See the Xenon documentation.

    :param files_scheme:
        The scheme by which to transfer files. Should be 'local' or 'ssh'.
        See the Xenon documentation.

    :param location:
        A location. This can be the host of the 'ssh' or 'slurm' server.

    :param credential:
        To enter a server through ssh, we need to have some credentials.
        Preferably, you have a private/public key pair by which you can
        identify yourself. Otherwise, this would be a combination of
        username/password. This functions that can create a credential
        object can be found in Xenon.credentials in the Xenon documentation.

    :param jobs_properties:
        Configuration to the Xenon.jobs module.

    :param files_properties:
        Configuration to the Xenon.files module.
    """
    def __init__(self, *, name=None, scheduler_adaptor='local',
                 location=None, credential=None, jobs_properties=None,
                 files_properties=None):
        self.name = name or ("xenon-" + str(uuid.uuid4()))
        self.scheduler_adaptor = scheduler_adaptor
        self.location = location
        self.credential = credential
        self.jobs_properties = jobs_properties
        self.files_properties = files_properties
        self._scheduler = None
        self._file_system = None

    @property
    def scheduler_args(self):
        args = {'adaptor': self.scheduler_adaptor,
                'location': self.location,
                'properties': self.jobs_properties}

        if isinstance(self.credential, xenon.PasswordCredential):
            args['password_credential'] = self.credential
        if isinstance(self.credential, xenon.CertificateCredential):
            args['certificate_credential'] = self.credential

        return args

    @property
    def scheduler(self):
        """Returns the scheduler object."""
        if self._scheduler is None:
            self._scheduler = xenon.Scheduler.create(**self.scheduler_args)

        return self._scheduler

    @property
    def file_system(self):
        """Gets the filesystem corresponding to the open scheduler."""
        if self._file_system is None:
            self._file_system = self.scheduler.get_file_system()

        return self._file_system
