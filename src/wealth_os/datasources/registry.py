from __future__ import annotations

from typing import Dict, Type

from .base import PriceDataSource, TxImportSource


_PRICE_SOURCES: Dict[str, Type[PriceDataSource]] = {}
_IMPORT_SOURCES: Dict[str, Type[TxImportSource]] = {}


def register_price_source(cls: Type[PriceDataSource]) -> Type[PriceDataSource]:
    _PRICE_SOURCES[cls.id()] = cls
    return cls


def register_import_source(cls: Type[TxImportSource]) -> Type[TxImportSource]:
    _IMPORT_SOURCES[cls.id()] = cls
    return cls


def get_price_sources() -> Dict[str, Type[PriceDataSource]]:
    return dict(_PRICE_SOURCES)


def get_price_source_cls(name: str) -> Type[PriceDataSource] | None:
    return _PRICE_SOURCES.get(name)


def get_import_sources() -> Dict[str, Type[TxImportSource]]:
    return dict(_IMPORT_SOURCES)
