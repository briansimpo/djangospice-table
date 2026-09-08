from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from django import forms
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

    # ------------------------------------------------------------------
    # Endpoint
    # ------------------------------------------------------------------

    @property
    def endpoint(self) -> str:
        url = reverse(
            self.namespace,
            kwargs={
                APP_NAME_KEY: self.app_label,
                MODEL_NAME_KEY: self.name,
            },
        )

        params = {
            key: value
            for key, value in self.kwargs.items()
            if key != "id"
        }

        return f"{url}?{urlencode(params)}" if params else url

    # ------------------------------------------------------------------
    # Definition
    # ------------------------------------------------------------------

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
                row["actions"] = self.get_row_actions()

            rows.append(row)

        return rows

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def get_filters(self) -> list[dict[str, Any]]:
        """
        Return declarative filter definitions for the client.

        A filter whose Django form widget exposes lookup metadata is
        represented as a remote lookup filter.

        DataTable does not import or depend on the lookup package.
        """
        if not self.filterset:
            return []

        return [
            self.serialize_filter(name, field)
            for name, field in self.filterset.filters.items()
        ]

    def serialize_filter(self, name: str,field: Any) -> dict[str, Any]:
        """
        Convert a django-filter filter into a declarative filter.
        """
        form_field = field.field
        widget = form_field.widget

        definition: dict[str, Any] = {
            "name": name,
            "type": self.get_filter_type(form_field),
            "label": str(field.label or name),
            "required": bool(form_field.required),
        }

        value = self.get_filter_value(name)

        if value is not None:
            definition["value"] = serialize(value)

        if self.is_lookup_widget(widget):
            return self.serialize_lookup_filter(
                definition,
                form_field,
                widget,
            )

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

    # ------------------------------------------------------------------
    # Lookup Filters
    # ------------------------------------------------------------------

    def is_lookup_widget(self, widget: Any) -> bool:
        """
        Determine whether a form widget exposes the lookup contract.

        This deliberately uses duck typing instead of importing a concrete
        LookupWidget class. DataTable therefore has no dependency on the
        lookup package.
        """
        return (
            hasattr(widget, "lookup_url")
            and hasattr(widget, "page_size")
            and hasattr(widget, "min_search_length")
        )

    def serialize_lookup_filter(self, definition: dict[str, Any], field: forms.Field, widget: Any) -> dict[str, Any]:
        """
        Serialize the public lookup configuration exposed by a form widget.
        """
        definition["type"] = "lookup"
        definition["multiple"] = self.is_multi_select(
            field,
            widget,
        )

        source: dict[str, Any] = {
            "type": "remote",
            "endpoint": widget.lookup_url,
            "searchable": True,
            "page_size": widget.page_size,
        }

        if widget.min_search_length:
            source["min_search_length"] = widget.min_search_length

        config = getattr(widget, "config", None)

        if config is not None:
            search_param = getattr(
                config,
                "search_param",
                None,
            )

            page_param = getattr(
                config,
                "page_param",
                None,
            )

            page_size_param = getattr(
                config,
                "page_size_param",
                None,
            )

            if search_param:
                source["search_parameter"] = search_param

            if page_param:
                source["page_parameter"] = page_param

            if page_size_param:
                source["page_size_parameter"] = page_size_param

        definition["source"] = source

        placeholder = getattr(
            widget,
            "placeholder",
            None,
        )

        if placeholder:
            definition["placeholder"] = placeholder

        search_placeholder = getattr(
            widget,
            "search_placeholder",
            None,
        )

        if search_placeholder:
            definition["search_placeholder"] = search_placeholder

        definition["allow_clear"] = getattr(
            widget,
            "allow_clear",
            True,
        )

        dependencies = self.get_lookup_dependencies(widget)

        if dependencies:
            definition["dependencies"] = dependencies

        return definition

    def get_lookup_dependencies(self, widget: Any) -> list[str]:
        """
        Return dependency paths exposed by a lookup-capable widget.
        """
        resolver = getattr(
            widget,
            "get_lookup_dependencies",
            None,
        )

        if callable(resolver):
            return list(resolver())

        dependencies = getattr(
            widget,
            "dependencies",
            (),
        )

        return [
            getattr(
                dependency,
                "path",
                dependency,
            )
            for dependency in dependencies
        ]

    def is_multi_select(self, field: forms.Field, widget: Any) -> bool:
        """
        Determine whether the filter is a multi-select lookup.
        """
        explicit = getattr(
            widget,
            "multi_select",
            None,
        )

        if explicit is not None:
            return bool(explicit)

        if isinstance(
            field,
            (
                forms.ModelMultipleChoiceField,
                forms.MultipleChoiceField,
            ),
        ):
            return True

        return bool(
            getattr(widget, "attrs", {}).get("multiple")
        )

    # ------------------------------------------------------------------
    # Filter Value
    # ------------------------------------------------------------------

    def get_filter_value(self, name: str) -> Any:
        """
        Return the current value for a filter.

        The Django form remains the source of truth for filter state.
        """
        if not self.filterset:
            return None

        form = self.filterset.form

        if name not in form.fields:
            return None

        if not form.is_bound:
            return form.fields[name].initial

        return form[name].value()

    # ------------------------------------------------------------------
    # Filter Type
    # ------------------------------------------------------------------

    def get_filter_type(self, field: forms.Field) -> str:
        """
        Return the declarative filter type.

        This deliberately uses Django form field characteristics rather
        than introducing a second filter abstraction.
        """
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
            "table": self.serialize_actions(
                self.get_table_actions()
            ),
            "row": self.serialize_actions(
                self.get_row_actions()
            ),
            "bulk": self.serialize_actions(
                self.get_bulk_actions()
            ),
        }

    def serialize_actions(self, actions: Any) -> list[dict[str, Any]]:
        """
        Serialize an Actions collection into declarative action metadata.

        The existing action infrastructure remains responsible for the
        action objects themselves.
        """
        if not actions:
            return []

        return [
            self.serialize_action(action)
            for action in actions
        ]

    def serialize_action(self, action: Any) -> dict[str, Any]:
        """
        Convert an action into client-facing metadata.
        """
        if hasattr(action, "to_dict") and callable(action.to_dict):
            return serialize(action.to_dict())

        definition: dict[str, Any] = {
            "name": getattr(
                action,
                "name",
                action.__class__.__name__,
            ),
        }

        label = getattr(
            action,
            "label",
            None,
        )

        if label is not None:
            definition["label"] = str(label)

        icon = getattr(
            action,
            "icon",
            None,
        )

        if icon is not None:
            definition["icon"] = icon

        return serialize(definition)

    def get_row_actions(self) -> list[dict[str, Any]]:
        """
        Return actions available for a specific row.

        Applications can override this to apply per-row permission or
        availability rules.
        """
        return self.serialize_actions(
            self.row_actions
        )

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    def get_response_data(self) -> dict[str, Any]:
        """
        Return the JSON-ready DataTable payload.
        """
        return serialize(
            self.get_definition()
        )