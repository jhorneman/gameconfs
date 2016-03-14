# -*- coding: utf-8 -*-

TESTING = True

SECRET_KEY = "DevSecretKey"

WTF_CSRF_ENABLED = False    # Or CSRF checks will fail.

SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
