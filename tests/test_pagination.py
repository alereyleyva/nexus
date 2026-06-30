from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.common.errors import BadRequestError
from app.common.pagination import Cursor, decode_cursor, encode_cursor, filter_hash
from app.modules.memory_entries.service import MemoryEntryService
from tests.conftest import SeedData, actor, memory_request


def test_cursor_validates_filter_consistency() -> None:
    first_hash = filter_hash({"project_id": "one"})
    cursor = encode_cursor(Cursor(sort_values=["2026-01-01", "id"], filter_hash=first_hash))
    decoded = decode_cursor(cursor, expected_filter_hash=first_hash)
    assert decoded.sort_values == ["2026-01-01", "id"]
    with pytest.raises(BadRequestError):
        decode_cursor(cursor, expected_filter_hash=filter_hash({"project_id": "two"}))


def test_memory_list_uses_limit_and_page_metadata(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    for index in range(3):
        service.create_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
            request=memory_request(title=f"Memory {index}", body="body"),
        )
    page = service.list_memory(actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), limit=2)
    assert len(page.items) == 2
    assert page.page.has_more is True
