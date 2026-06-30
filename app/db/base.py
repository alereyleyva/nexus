from __future__ import annotations

from importlib import import_module

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def load_all_models() -> None:
    for module_name in (
        "app.modules.audit.models",
        "app.modules.auth.models",
        "app.modules.groups.models",
        "app.modules.identity.models",
        "app.modules.memory_entries.models",
        "app.modules.projects.models",
    ):
        import_module(module_name)
