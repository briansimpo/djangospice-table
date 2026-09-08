from __future__ import annotations

import uuid
from typing import Any
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django_tables2.export import TableExport


class TableExporter:
    """
    Responsible for table data extraction, formatting, naming conventions,
    and direct storage persistence.
    """

    def __init__(self,  table: Any, export_format: str, rename_file: bool = False) -> None:
        self.table = table
        self.export_format = export_format
        self.rename_file = rename_file

    def _generate_filename(self) -> str:
        """Determines the output filename based on table or model metadata."""
        meta = getattr(self.table, "Meta", None)
        model = getattr(meta, "model", None)
        
        base_name = self.table.__class__.__name__ or (
            model.__name__ if model else "export"
        )
        clean_name = base_name.lower().replace("table", "").strip("_")

        if self.rename_file:
            return f"exports/{clean_name}_{uuid.uuid4().hex[:8]}.{self.export_format}"
        
        return f"exports/{clean_name}.{self.export_format}"

    def export(self) -> tuple[str, str]:
        """Renders, writes, and saves the file, returning (file_path, file_url)."""
        exporter = TableExport(self.export_format, self.table)
        file_content = exporter.export()
        filename = self._generate_filename()

        file_path = default_storage.save(filename, ContentFile(file_content))
        file_url = default_storage.url(file_path)

        return file_path, file_url