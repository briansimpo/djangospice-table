from __future__ import annotations

import django_tables2 as tables

from djangospice_table.widget import TableWidget
from djangospice_table.columns import RowActionsColumn
from .page import TablePaginationComposer


class TableComposer:
    """
    Builds and configures a django-tables2 table.
    """

    def __init__(self, widget: TableWidget) -> None:
        self.widget = widget

    def get_class(self) -> type[tables.Table]:
        widget = self.widget

        if widget.table_class is not None:
            table_class = widget.table_class

        else:
            if widget.model is None:
                raise ValueError(
                    f"{widget.__class__.__name__} requires either "
                    "'table_class' or 'model'."
                )

            table_class = tables.table_factory(
                widget.model,
                fields=widget.fields,
                exclude=widget.exclude,
            )

        if not widget.row_actions:
            return table_class

        return type(
            f"{table_class.__name__}WidgetTable",
            (table_class,),
            {
                "row_actions": RowActionsColumn(
                    verbose_name="",
                    orderable=False,
                ),
            },
        )

    def compose(self, queryset) -> tables.Table:
        widget = self.widget

        table = self.get_class()(
            queryset,
            request=widget.request,
        )

        table.widget = widget

        TablePaginationComposer(
            request=widget.request,
            config=widget.pagination_config,
        ).configure(table)

        return table