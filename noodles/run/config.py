import configparser
from typing import (List)
from ..utility import (look_up)


runners = [
    # ======================================================================= #
    #  Single threaded runners
    # ======================================================================= #
    {
        'name': 'single',
        'features': [],
        'description': """
            Run a workflow in a single thread. This is the absolute minimal
            runner, consisting of a single queue for jobs and a worker running
            jobs every time a result is pulled.""",
        'command': 'noodles.run.single',
        'arguments': {}
    },

    {
        'name': 'single',
        'features': ['display'],
        'description': """
            Adds a display to the single runner. Everything still runs in a
            single thread. Every time a job is pulled by the worker, a message
            goes to the display routine; when the job is finished the result is
            sent to the display routine.""",
        'command': 'noodles.run.single_with_display',
        'arguments': {
            'display': {
                'default': 'noodles.display.NCDisplay',
                'reader':  'look-up',
                'help': 'the display routine'
            }
         }
    },

    # ======================================================================= #
    #  Multi-threaded runners
    # ======================================================================= #
    {
        'name': 'parallel',
        'features': [],
        'command': 'noodles.run.parallel',
        'arguments': {
            'n_threads': {
                'default': '1',
                'reader': 'integer'
            }
        }
    },

    {
        'name': 'parallel',
        'features': ['display'],
        'command': 'noodles.run.parallel_with_display',
        'arguments': {
            'n_threads': {
                'default': '1',
                'reader': 'integer'
            },
            'display': {
                'default': 'noodles.display.NCDisplay',
                'reader':  'look-up'
            }
        }
    },

    {
        'name': 'parallel',
        'features': ['prov', 'display'],
        'description': """
            Run a workflow in `n_threads` parallel threads. Now we replaced the
            single worker with a thread-pool of workers.

            This version works with the JobDB to cache results; however we only
            store the jobs that are hinted with the 'store' keyword, unless
            `cache_all` is set to `True`.""",
        'command': 'noodles.run.run_with_prov.run_parallel_opt',
        'arguments': {
            'n_threads': {
                'default': '1',
                'reader': 'integer',
                'help': 'the number of threads to run'
            },
            'registry': {
                'default': 'noodles.serial.base',
                'reader': 'look-up',
                'help': 'the serialisation registry to use'
            },
            'display': {
                'default': 'noodles.display.NCDisplay',
                'reader':  'look-up',
                'help': 'the display to use'
            },
            'database': {
                'default': 'TinyDB',
                'help': 'the database backend for the job cache'
            },
            'cache_file': {
                'default': 'cache.json',
                'help': 'the file used to store the job cache'
            },
            'cache_all': {
                'default': 'False',
                'reader': 'boolean',
                'help': 'set this if you want to store all jobs in cache'
            }
        }
    },

    {
        'name': 'xenon',
        'features': ['prov', 'display'],
        'command': 'noodles.run.xenon.run_xenon_prov',
        'arguments': {
        }
    },

    {
        'name': 'process',
        'features': ['msgpack'],
        'command': 'noodles.run.process.run_process',
        'arguments': {
        }
    }
]


def find_runner(name: str, features: List[str]) -> str:
    name_candidates = filter(
        lambda r: r['name'] == name,
        runners)
    feature_candidates = filter(
        lambda r: all(f in r['features'] for f in features),
        name_candidates)
    return min(feature_candidates, lambda r: len(r['features']))


def run_with_config(config_file, workflow, machine=None):
    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation())
    config.read(config_file)

    machine = config.get('default', 'machine', fallback=machine)
    if machine is None:
        print("No machine given, running local in single thread.")
        runner = find_runner(name='single', features=[])
        settings = {}

    else:
        M = config['Machines']
        runner_name = M.get(machine, 'runner')
        features = map(str.strip, M.get(machine, 'features').split(','))
        runner = find_runner(name=runner_name, features=features)
        settings = dict(M[machine])

        del settings['runner']
        del settings['features']

        if 'user' in settings:
            settings['user'] = dict(config['Users'][settings['user']])

    run = look_up(runner['command'])

    return run(workflow, **settings)
