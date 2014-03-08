import bmemcached


class TimeoutFixCacheClient(bmemcached.Client):
    def __init__(self, *args, **kwargs):
        super(TimeoutFixCacheClient, self).__init__(*args, **kwargs)

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):
            def wrapped(*args, **kwargs):
                if 'timeout' in kwargs:
                    kwargs['time'] = kwargs['timeout']
                    del kwargs['timeout']
                result = attr(*args, **kwargs)
                return result
            return wrapped
        else:
            return attr


def bmemcached_cache(app, config, args, kwargs):
    return TimeoutFixCacheClient(servers=config['CACHE_MEMCACHED_SERVERS'],
                          username=config['CACHE_MEMCACHED_USERNAME'],
                          password=config['CACHE_MEMCACHED_PASSWORD'])


def set_up_cache(_app):
    from flask.ext.cache import Cache
    try:
        _app.cache = Cache(_app)
    except EnvironmentError, e:
        if e.errno == 61:
            _app.logger.error("Couldn't connect to memcached - switching to null cache")
            _app.config["CACHE_TYPE"] = "null"
            _app.cache = Cache(_app)
        else:
            raise e
