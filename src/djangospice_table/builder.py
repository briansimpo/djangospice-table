from __future__ import annotations

from typing import Any, Type
from django.db import models

from djangospice_framework.core.serializer import resolve_class, deserialize
from djangospice_framework.filters.helpers import dynamic_queryset


class TableBuilder:
    """
    Responsible for class resolution, queryset evaluation, dynamic filtering,
    and compiling the final Django Table instance.
    """

    def __init__(self, table_class: str | Type[Any], model_class: str | Type[models.Model], filters: dict[str, Any] | None = None, serialized_queryset: dict[str, Any] | None = None) -> None:
        # Resolve class paths dynamically if passed as strings (LRU cached)
        self.table_class = (
            resolve_class(table_class) if isinstance(table_class, str) else table_class
        )
        self.model_class = (
            resolve_class(model_class) if isinstance(model_class, str) else model_class
        )
        self.filters = filters or {}
        self.serialized_queryset = serialized_queryset

    def build_queryset(self) -> models.QuerySet:
        """Assembles the filtered queryset."""
        # Scenario A: Hydrate a pre-serialized collection reference
        if self.serialized_queryset:
            return deserialize(self.serialized_queryset)

        # Scenario B: Build fresh query and apply dynamic lookup dictionary
        qs = self.model_class.objects.all()
        return dynamic_queryset(qs, self.filters)

    def build_table(self) -> Any:
        """Returns an instantiated Django Table ready for rendering or export."""
        queryset = self.build_queryset()
        return self.table_class(queryset)