import os


def load_env(key, default=None):
    if key in os.environ:
        return os.environ[key]
    else:
        return default
