from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from psycopg import Connection, connect
from psycopg.rows import dict_row

from api_service.config import Settings


@contextmanager
def open_connection(settings: Settings) -> Iterator[Connection]:
    with connect(settings.database_url, row_factory=dict_row) as connection:
        yield connection
