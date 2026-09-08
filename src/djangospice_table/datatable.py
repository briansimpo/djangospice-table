from __future__ import annotations

from typing import Any
from urllib.parse import urlencode
from django.urls import reverse
from djangospice_framework.core.serializer import serialize
from djangospice_widget.conf import APP_NAME_KEY, MODEL_NAME_KEY

from .widget import TableWidget


class DataTable(TableWidget):
    """
    Server-side dynamic table.

    Extends TableWidget with a declarative representation of the current
    table state suitable for JSON responses and client-side rendering.

    TableWidget remains responsible for:
        - queryset construction
        - filtering
        - searching
        - sorting
        - pagination
        - django-tables2 table construction
        - actions

    DataTable is only responsible for exposing that state as a
    declarative table definition.
    """

    type = "table"

    template = "djangospice_table/datatable.html"

    @property
    def endpoint(self) -> str:
        url = reverse(
            self.namespace,
            kwargs={
                APP_NAME_KEY: self.app_label,
                MODEL_NAME_KEY: self.name,
            },
        )
        params = {k: v for k, v in self.kwargs.items() if k != "id"}
        return f"{url}?{urlencode(params)}" if params else url

    def get_definition(self) -> dict[str, Any]:
        """
        Return the complete declarative table definition.
        """
        return {
            "type": self.type,
            "id": self.id,
            "configuration": self.get_configuration(),
            "columns": self.get_columns(),
            "rows": self.get_rows(),
            "filters": self.get_filters(),
            "search": self.get_search(),
            "sorting": self.get_sorting(),
            "pagination": self.get_pagination(),
            "actions": self.get_actions(),
        }

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def get_configuration(self) -> dict[str, Any]:
        return {
            "selectable": self.selectable,
            "searchable": self.show_search and bool(self.search_fields),
            "sortable": True,
            "filterable": self.show_filters and bool(self.filterset),
            "pagination": self.pagination_config.enabled,
            "page_size": self.pagination_config.page_size,
            "page_size_options": list(
                self.pagination_config.page_size_options
            ),
        }

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    def get_columns(self) -> list[dict[str, Any]]:
        """
        Return the columns exposed by django-tables2.

        Rendering concerns remain on the client. The server only describes
        the column metadata and provides the corresponding row values.
        """
        columns: list[dict[str, Any]] = []

        for name, column in self.table.columns.items():
            columns.append(
                {
                    "name": name,
                    "label": str(column.header),
                    "orderable": bool(column.orderable),
                }
            )

        return columns

    # ------------------------------------------------------------------
    # Rows
    # ------------------------------------------------------------------

    def get_rows(self) -> list[dict[str, Any]]:
        """
        Serialize the currently visible table rows.

        Values are passed through the framework serializer so DataTable
        does not maintain its own serialization rules.
        """
        rows: list[dict[str, Any]] = []

        for record in self.table.data:
            row = {
                column.name: serialize(
                    column.accessor.resolve(record)
                )
                for column in self.table.columns
            }

            row["id"] = serialize(record.pk)

            if self.row_actions:
                row["actions"] = self.get_row_actions(record)

            rows.append(row)

        return rows

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def get_filters(self) -> list[dict[str, Any]]:
        """
        Return filter definitions for the client.

        Filter widgets may expose a remote lookup configuration rather
        than embedding their complete option set in the table payload.
        """
        if not self.filterset:
            return []

        filters: list[dict[str, Any]] = []

        for name, field in self.filterset.filters.items():
            filters.append(self.serialize_filter(name, field))

        return filters

    def serialize_filter(
        self,
        name: str,
        field: Any,
    ) -> dict[str, Any]:
        """
        Convert a django-filter field into a declarative filter.

        Subclasses can override this for application-specific filter
        metadata or lookup-backed filters.
        """
        form_field = field.field

        definition: dict[str, Any] = {
            "name": name,
            "type": self.get_filter_type(form_field),
            "label": str(field.label or name),
            "required": bool(form_field.required),
        }

        choices = getattr(form_field, "choices", None)

        if choices:
            definition["choices"] = [
                {
                    "value": serialize(value),
                    "label": str(label),
                }
                for value, label in choices
            ]

        return definition

    def get_filter_type(self, field: Any) -> str:
        """
        Return the declarative filter type.

        This deliberately uses Django form field characteristics rather
        than introducing a second filter abstraction.
        """
        from django import forms

        if isinstance(field, forms.BooleanField):
            return "boolean"

        if isinstance(field, forms.MultipleChoiceField):
            return "multi_choice"

        if isinstance(field, forms.ChoiceField):
            return "choice"

        if isinstance(field, forms.DateTimeField):
            return "datetime"

        if isinstance(field, forms.DateField):
            return "date"

        if isinstance(field, forms.DecimalField):
            return "decimal"

        if isinstance(field, forms.IntegerField):
            return "integer"

        return "text"

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def get_search(self) -> dict[str, Any]:
        return {
            "enabled": self.show_search and bool(self.search_fields),
            "parameter": self.search.parameter,
            "value": self.search.value,
        }

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def get_sorting(self) -> dict[str, Any]:
        """
        Return the current django-tables2 ordering.
        """
        order_by = self.table.order_by

        if isinstance(order_by, str):
            order_by = (order_by,)

        return {
            "parameter": self.table.order_by_field,
            "value": list(order_by or ()),
        }

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def get_pagination(self) -> dict[str, Any] | None:
        if self.pagination_state is None:
            return None

        return self.pagination_state.to_dict()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def get_actions(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "table": self.serialize_actions(self.get_table_actions()),
            "row": self.serialize_actions(self.get_row_actions()),
            "bulk": self.serialize_actions(self.get_bulk_actions()),
        }

    def serialize_actions(self, actions: Any) -> list[dict[str, Any]]:
        """
        Serialize an Actions collection into declarative action metadata.

        The exact action object remains owned by the existing action
        infrastructure. This method only exposes its public metadata.
        """
        if not actions:
            return []

        result: list[dict[str, Any]] = []

        for action in actions:
            result.append(self.serialize_action(action))

        return result

    def serialize_action(self, action: Any) -> dict[str, Any]:
        """
        Convert an action into client-facing metadata.

        Action implementations can expose additional metadata through
        ``to_dict()``. Otherwise the common public attributes are used.
        """
        if hasattr(action, "to_dict") and callable(action.to_dict):
            return serialize(action.to_dict())

        definition: dict[str, Any] = {
            "name": getattr(action, "name", action.__class__.__name__),
        }

        label = getattr(action, "label", None)

        if label is not None:
            definition["label"] = str(label)

        icon = getattr(action, "icon", None)

        if icon is not None:
            definition["icon"] = icon

        return serialize(definition)

    def get_row_actions(self, record: Any) -> list[dict[str, Any]]:
        """
        Return actions available for a specific row.

        The default implementation exposes the configured row actions.
        Applications can override this to apply per-row permission or
        availability rules.
        """
        return self.serialize_actions(self.row_actions)

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    def get_response_data(self) -> dict[str, Any]:
        """
        Return the JSON-ready DataTable payload.
        """
        return serialize(self.get_definition())