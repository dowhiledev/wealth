"""Datasources package: registers available providers on import."""

# Import providers to trigger registry decorators
from . import coinmarketcap as _cmc  # noqa: F401
from . import generic_csv as _gcsv  # noqa: F401
from . import coindesk_legacy as _cd  # noqa: F401

__all__ = []
