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
    _app.cache = Cache()
    _app.cache.init_app(_app, config={
        'CACHE_TYPE': 'gameconfs.caching.bmemcached_cache',
        'CACHE_MEMCACHED_SERVERS': ['0.0.0.0:11211'],
        'CACHE_MEMCACHED_USERNAME': None,
        'CACHE_MEMCACHED_PASSWORD': None
    })
