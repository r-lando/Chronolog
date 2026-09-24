"""
Cross-dialect column types.

Production runs on PostgreSQL, but the automated test suite uses an
in-memory SQLite database for speed and zero external dependencies.
Postgres-only types (postgresql.UUID, postgresql.JSONB) don't compile
under SQLite, so models use these portable wrappers instead. On
Postgres they behave exactly like the native UUID/JSONB types; on any
other dialect they fall back to a plain, well-understood representation.
"""

import uuid

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import CHAR, JSON, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent UUID column: native UUID on Postgres, CHAR(32) elsewhere."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class PortableJSON(TypeDecorator):
    """JSONB on Postgres, plain JSON elsewhere. Fine for data we never index/query inside."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
