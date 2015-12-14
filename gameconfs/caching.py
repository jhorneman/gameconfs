import logging
import bmemcached
from app_logging import add_logger


logger = logging.getLogger(__name__)
add_logger(logger)


# bmemcached (https://github.com/jaysonsantos/python-binary-memcached/blob/master/bmemcached/client.py)
# has a slightly different interface from what Flask-Cache expects
# so we need to fix this
# The 'timeout' keyword parameter is called 'time'
# The 'clean' method is called 'flush_all'

# Also, we catch most exceptions and quietly deal with them.
# RedisLabs' memcached does service maintenance about once a month, and this breaks the app if
# we don't catch it.
# set_servers is the connection method, and we want those exceptions to propagate.


class InterfaceFixCacheClient(bmemcached.Client):
    def __init__(self, *args, **kwargs):
        super(InterfaceFixCacheClient, self).__init__(*args, **kwargs)

    def __getattribute__(self, name):
        if name == "clear":
            name = "flush_all"
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):
            def wrapped(*args, **kwargs):
                if 'timeout' in kwargs:
                    kwargs['time'] = kwargs['timeout']
                    del kwargs['timeout']

                try:
                    result = attr(*args, **kwargs)
                except BaseException, e:
                    if name == "set_servers":
                        raise e
                    else:
                        logger.error("memcached error in method {0}: {1}.".format(name, str(e)))
                        result = None

                return result
            return wrapped
        else:
            return attr


def bmemcached_cache(app, config, args, kwargs):
    return InterfaceFixCacheClient(servers=config['CACHE_MEMCACHED_SERVERS'],
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
