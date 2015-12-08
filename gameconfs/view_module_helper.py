# -*- coding: utf-8 -*-


class DeferredRoutes(object):
    def __init__(self):
        self.routes = []

    def get_decorator(self):
        def decorator(rule, **options):
            def wrapper(f):
                self.store_route(rule, f, **options)
                return f
            return wrapper
        return decorator

    def store_route(self, rule, view_function, **options):
        self.routes.append((rule, view_function, options))

    def apply_routes(self, app_or_blueprint):
        for rule, view_function, options in self.routes:
            endpoint = options.pop('endpoint', None)
            app_or_blueprint.add_url_rule(rule, endpoint, view_function, **options)
