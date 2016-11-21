import configparser

config = {
    # call_by_value: keep this True unless you know what you're doing.
    # The functioning of the DelayedObject and Storable classes depend
    # on deep-copying arguments to scheduled functions.
    'call_by_value': True,
}


def read_config(filename: str):
    config = configparser.ConfigParser()
    config.read(filename)
    return config
