from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

from api_service.config import Settings

if TYPE_CHECKING:
    from psycopg import Connection
else:  # pragma: no cover - keeps unit tests lightweight when psycopg is unavailable.
    Connection = Any


@contextmanager
def open_connection(settings: Settings) -> Iterator[Connection]:
    from psycopg import connect
    from psycopg.rows import dict_row

    with connect(settings.database_url, row_factory=dict_row) as connection:
        yield connection
