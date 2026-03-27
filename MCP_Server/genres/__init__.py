"""Genre blueprint library: curated reference data for electronic music genres."""

from .catalog import get_blueprint, list_genres, resolve_alias
from .schema import GenreBlueprint, validate_blueprint

__all__ = [
    "get_blueprint",
    "list_genres",
    "resolve_alias",
    "GenreBlueprint",
    "validate_blueprint",
]
