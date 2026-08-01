from app.services.catalog.space_catalog import (
    CATALOG,
    SpaceType,
    UnknownSpaceType,
    get,
    register,
    resolve_alias,
    spaces_from_rooms,
)

__all__ = [
    "CATALOG",
    "SpaceType",
    "UnknownSpaceType",
    "get",
    "register",
    "resolve_alias",
    "spaces_from_rooms",
]
