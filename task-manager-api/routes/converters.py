from werkzeug.routing import IntegerConverter

from routes.validation import INT64_MAX


class BoundedIntegerConverter(IntegerConverter):
    """Path ids beyond what the database driver can bind do not match the route (404),
    instead of overflowing inside the driver (500)."""

    def __init__(self, url_map, *args, **kwargs):
        kwargs.setdefault('max', INT64_MAX)
        super().__init__(url_map, *args, **kwargs)
