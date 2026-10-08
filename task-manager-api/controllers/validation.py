"""Boundary type checks shared by the controllers (RP-11).

A JSON array or object where a scalar is stored cannot be written to the datastore: today it
ends as a server error. These checks turn that into a 400. They never reject a scalar that is
accepted today and never add limits or formats: those are product decisions.
"""
from models.errors import ValidationError


def reject_containers(value, message):
    if isinstance(value, (list, dict)):
        raise ValidationError(message)
