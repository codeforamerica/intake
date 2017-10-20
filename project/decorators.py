from functools import wraps
from django.conf import settings


def run_if_setting_true(setting_name, alternate_return_value):
    def true_decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not getattr(settings, setting_name, False):
                return alternate_return_value
            return func(*args, **kwargs)
        return wrapped
    return true_decorator
