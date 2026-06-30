from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects import postgresql

STRING_LIST = JSON().with_variant(postgresql.ARRAY(String()), "postgresql")
JSON_OBJECT = JSON().with_variant(postgresql.JSONB(), "postgresql")
SEARCH_VECTOR = Text().with_variant(postgresql.TSVECTOR(), "postgresql")
