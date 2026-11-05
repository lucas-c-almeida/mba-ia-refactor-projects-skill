from flask import Request
from werkzeug.exceptions import BadRequest


class JsonRequest(Request):
    """Keeps the 400 body for an undecodable JSON document stable: the parser's message about the
    caller's own input, which the framework only included while debug mode was on."""

    def on_json_loading_failed(self, e):
        if e is not None:
            raise BadRequest(f'Failed to decode JSON object: {e}')
        return super().on_json_loading_failed(e)
