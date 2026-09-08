from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Type
from django.db import models

from djangospice_framework.jobs import Job
from .builder import TableBuilder
from .exporter import TableExporter

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class TableExportJob(Job):
    """
    A lightweight, fully serializable background task runner.
    Coordinates TableBuilder and TableExporter execution on background workers.
    """
    table_class_path: str
    model_class_path: str
    export_format: str
    filters: dict[str, Any] = field(default_factory=dict)
    serialized_queryset: dict[str, Any] = field(default_factory=dict)
    rename_file: bool = False

    @classmethod
    def create(
        cls,
        table_class: Type[Any],
        model_class: Type[models.Model],
        export_format: str,
        filters: dict[str, Any] | None = None,
        serialized_queryset: dict[str, Any] | None = None,
        rename_file: bool = False,
        **kwargs
    ) -> TableExportJob:
        """Instantiates the serializable job configuration."""
        return cls(
            table_class_path=f"{table_class.__module__}.{table_class.__name__}",
            model_class_path=f"{model_class.__module__}.{model_class.__name__}",
            export_format=export_format,
            filters=filters or {},
            serialized_queryset=serialized_queryset or {},
            rename_file=rename_file,
            **kwargs
        )

    def handle(self) -> tuple[str, str]:
        """Executes inside the Celery worker thread."""
        logger.info(f"Assembling table background export for {self.table_class_path}")

        # 1. Coordinate Table Creation (Builder)
        builder = TableBuilder(
            table_class=self.table_class_path,
            model_class=self.model_class_path,
            filters=self.filters,
            serialized_queryset=self.serialized_queryset,
        )
        table = builder.build_table()

        # 2. Coordinate File Writing & Persistence (Exporter)
        exporter = TableExporter(
            table=table,
            export_format=self.export_format,
            rename_file=self.rename_file,
        )
        return exporter.export()