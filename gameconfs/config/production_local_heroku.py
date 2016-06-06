# -*- coding: utf-8 -*-

import os
from ..project import ADMIN_EMAIL


SECRET_KEY = "\xcb\xfe%\xff4\xd3l!)\x84o\xacIB6\x1c\x1f\xa5\xa2\xea\x9f\x0b\xf1\xf0"

# Get configuration data from Heroku environment variables.
# For local Heroku, these are set in the .env file.

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

CACHE_TYPE = "null"
# Or set local memcached parameters in .env and reactivate this:
# CACHE_MEMCACHED_SERVERS = os.environ.get("MEMCACHEDCLOUD_SERVERS").split(",")
# CACHE_MEMCACHED_USERNAME = os.environ.get("MEMCACHEDCLOUD_USERNAME")
# CACHE_MEMCACHED_PASSWORD = os.environ.get("MEMCACHEDCLOUD_PASSWORD")

MAIL_SERVER = os.environ.get("POSTMARK_SMTP_SERVER")
MAIL_USERNAME = os.environ.get("POSTMARK_API_TOKEN")
MAIL_PASSWORD = os.environ.get("POSTMARK_API_TOKEN")
MAIL_DEFAULT_SENDER = ADMIN_EMAIL
MAIL_USE_TLS = True
