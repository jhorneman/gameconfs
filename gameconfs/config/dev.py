# -*- coding: utf-8 -*-

DEBUG = True

SECRET_KEY = "DevSecretKey"

SQLALCHEMY_DATABASE_URI = "postgresql://gameconfs@localhost:5432/gameconfs"

# CACHE_TYPE = "gameconfs.caching.bmemcached_cache"
# CACHE_MEMCACHED_SERVERS = ["0.0.0.0:11211"]
# CACHE_MEMCACHED_USERNAME = None
# CACHE_MEMCACHED_PASSWORD = None

MAIL_PORT = 1025

# Stop Flask-Debug Toolbar from intercepting redirects, because it's annoying.
DEBUG_TB_INTERCEPT_REDIRECTS = False
