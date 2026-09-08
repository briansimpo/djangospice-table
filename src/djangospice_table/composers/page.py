from __future__ import annotations

import django_tables2 as tables

from djangospice_widget.pagination import PaginationConfig, PaginationState


class TablePaginationComposer:
    """
    Applies generic pagination configuration to a django-tables2 table.
    """

    def __init__(
        self,
        *,
        request,
        config: PaginationConfig,
    ) -> None:
        self.request = request
        self.config = config

    def configure(self, table: tables.Table) -> tables.Table:
        if not self.config.enabled:
            return table

        tables.RequestConfig(
            self.request,
            paginate={
                "per_page": self.config.page_size,
            },
        ).configure(table)

        return table


class TablePageComposer:
    """
    Converts django-tables2 pagination information into the generic
    PaginationState representation.
    """

    def __init__(
        self,
        *,
        table: tables.Table,
        config: PaginationConfig,
    ) -> None:
        self.table = table
        self.config = config

    def compose(self) -> PaginationState | None:
        if not self.config.enabled:
            return None

        page = self.table.page
        paginator = self.table.paginator

        return PaginationState(
            page=page.number,
            page_size=self.config.page_size,
            total=paginator.count,
            pages=paginator.num_pages,
            has_next=page.has_next(),
            has_previous=page.has_previous(),
            next_page=(
                page.next_page_number()
                if page.has_next()
                else None
            ),
            previous_page=(
                page.previous_page_number()
                if page.has_previous()
                else None
            ),
            first_page=(
                1
                if page.number > 1
                else None
            ),
            last_page=(
                paginator.num_pages
                if page.number < paginator.num_pages
                else None
            ),
            page_size_options=self.config.page_size_options,
            page_parameter=self.config.page_parameter,
            page_size_parameter=self.config.page_size_parameter,
        )