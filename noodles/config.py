
config = {
    # call_by_value: keep this True unless you know what you're doing.
    # The functioning of the DelayedObject and Storable classes depend
    # on deep-copying arguments to scheduled functions.
    'call_by_value': True,

    # use_prov: compute a MD5 hash of job descriptions and keep a database
    # with the results. This is made optional, since it creates a computational
    # overhead.
    'use_prov': True,

    # prov_serialiser: use this serialiser to compute the MD5 hash that
    # generates the key used to identify jobs and workflows in the provenance
    # database. Only has an effect if use_prov is True.
    'prov_serialiser': 'noodles.serial.base'
}
