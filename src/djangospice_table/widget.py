from __future__ import annotations

from typing import Any, ClassVar

import django_filters
import django_tables2 as tables
from django.db.models import Q, QuerySet

from djangospice_widget.actions import  ActionContext, Actions, BoundAction
from djangospice_widget.widget import Widget

from .columns import RowActionsColumn
from .page import PageContext


class TableWidget(Widget):
    """Reusable, request-aware table widget built on `django-tables2`.

    Combines queryset filtering (`django-filters`), full-text search, 
    pagination, row selection, and action bindings into a reactive HTMX widget.
    """

    # ------------------------------------------------------------------
    # Table Configuration
    # ------------------------------------------------------------------

    template_name = "djangospice_table/table.html"

    table_class: ClassVar[type[tables.Table] | None] = None
    """Custom django-tables2 Table class to render."""

    fields: ClassVar[tuple[str, ...] | str | None] = None
    """Explicit list of fields to include when auto-generating a table class."""

    exclude: ClassVar[tuple[str, ...] | str | None] = None
    """Explicit list of fields to exclude when auto-generating a table class."""

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    actions: ClassVar[Actions] = Actions()
    """Global table actions displayed in the toolbar (e.g., Create, Export)."""

    row_actions: ClassVar[Actions] = Actions()
    """Per-row actions rendered in a trailing action column (e.g., Edit, Delete)."""

    bulk_actions: ClassVar[Actions] = Actions()
    """Batch actions executed against selected row items."""

    # Context menu ------------------------------------------------------

    context_menu: ClassVar[bool] = True
    context_menu_actions: ClassVar[Actions | None] = None

    show_header: ClassVar[bool] = True
    show_footer: ClassVar[bool] = True

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    search_fields: ClassVar[tuple[str, ...]] = ()
    """Model field names to query using `icontains` lookup during search."""

    search_parameter: ClassVar[str] = "q"
    """GET parameter key used for receiving search input."""

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    filterset_class: ClassVar[type[django_filters.FilterSet] | None] = None
    """FilterSet class used for multi-field filtering."""

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    page_size_options: ClassVar[tuple[int, ...]] = (
        10,
        20,
        50,
        100,
        500,
    )

    paginate: ClassVar[bool] = True
    """Toggles pagination on or off."""

    paginate_by: ClassVar[int] = 20
    """Default number of items per page."""

    max_page_size: ClassVar[int] = 100
    """Upper limit constraint for user-specified page size parameter."""

    page_parameter: ClassVar[str] = "page"
    """GET query parameter key for page numbers."""

    page_size_parameter: ClassVar[str] = "page_size"
    """GET query parameter key for requested page size."""

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    selectable: ClassVar[bool] = False
    """Enables multi-row selection checkboxes."""

    selection_parameter: ClassVar[str] = "selected_ids"
    """Form field name used for bulk selection checkboxes."""

    # ------------------------------------------------------------------
    # UI Customization
    # ------------------------------------------------------------------

    toolbar: ClassVar[bool] = True
    """Toggles the rendering of the top action/search toolbar."""

    show_search: ClassVar[bool] = True
    """Toggles visibility of the search input component."""

    show_filters: ClassVar[bool] = True
    """Toggles visibility of the filter controls."""

    empty_message: ClassVar[str] = "No records found."
    """Fallback text rendered when table contains no records."""

    context_menu: ClassVar[bool] = True
    
    # ------------------------------------------------------------------
    # Runtime State
    # ------------------------------------------------------------------

    table: tables.Table
    filterset: django_filters.FilterSet | None

    # ==================================================================
    # Element IDs & Targets
    # ==================================================================

    @property
    def table_id(self) -> str:
        """HTML `id` attribute for the root `<table>` element."""
        return f"{self.name}-table"

    @property
    def content_id(self) -> str:
        """HTML `id` attribute for the dynamic content container swapped via HTMX."""
        return f"{self.name}-content"

    @property
    def selection_id(self) -> str:
        """HTML `id` attribute for the bulk selection container/form."""
        return f"{self.name}-selection"

    @property
    def htmx_target(self) -> str:
        """CSS selector targeting the dynamic HTMX update container."""
        return f"#{self.content_id}"
    
    @property
    def htmx_indicator(self):
        """Loader instance that should be shown during that HTMX request"""
        return f"{self.name}-loader"

    @property
    def context_menu_id(self) -> str:
        return f"{self.name}-context-menu"

    @property
    def page_size_id(self) -> str:
        return f"{self.table_id}-page-size"


    # ==================================================================
    # Lifecycle Methods
    # ==================================================================

    def initialize(self) -> None:
        """Initializes default runtime attribute state."""
        super().initialize()
        self.filterset = None

    def configure(self) -> None:
        """Executes table construction and configuration hooks."""
        super().configure()
        self.table = self.build_table()

    # ==================================================================
    # Queryset Processing
    # ==================================================================

    def get_table_queryset(self) -> QuerySet[Any]:
        """Resolves, filters, and searches the primary queryset.

        Returns:
            The fully processed `QuerySet` ready for table binding.
        """
        queryset = self.get_queryset()
        queryset = self.apply_filters(queryset)
        queryset = self.apply_search(queryset)
        return queryset

    # ==================================================================
    # Filtering Logic
    # ==================================================================

    def get_filterset_class(self) -> type[django_filters.FilterSet] | None:
        """Retrieves the configured `FilterSet` class.

        Returns:
            The `FilterSet` subclass or `None` if not set.
        """
        return self.filterset_class

    def get_filterset(self, queryset: QuerySet[Any]) -> django_filters.FilterSet | None:
        """Instantiates the `FilterSet` with current request data and queryset.

        Args:
            queryset: The base `QuerySet` to be filtered.

        Returns:
            An active `FilterSet` instance or `None` if no class is declared.
        """
        filterset_class = self.get_filterset_class()

        if filterset_class is None:
            return None

        return filterset_class(
            data=self.request.GET if self.request else None,
            queryset=queryset,
            request=self.request,
        )

    def apply_filters(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        """Applies configured filter rules to the given queryset.

        Args:
            queryset: The input `QuerySet`.

        Returns:
            Filtered `QuerySet` (or original if filters do not apply).
        """
        self.filterset = self.get_filterset(queryset)

        if self.filterset is None:
            return queryset

        return self.filterset.qs

    # ==================================================================
    # Search Logic
    # ==================================================================

    def get_search_term(self) -> str:
        """Extracts and sanitizes the search query term from request parameters.

        Returns:
            Cleaned search term string, or an empty string if not present.
        """
        if self.request is None:
            return ""

        return self.request.GET.get(self.search_parameter, "").strip()

    def apply_search(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        """Applies `icontains` OR lookup queries across configured `search_fields`.

        Args:
            queryset: The `QuerySet` to search against.

        Returns:
            Filtered `QuerySet` matching the search terms.
        """
        term = self.get_search_term()

        if not term or not self.search_fields:
            return queryset

        query = Q()
        for field in self.search_fields:
            query |= Q(**{f"{field}__icontains": term})

        return queryset.filter(query)

    # ==================================================================
    # Table Construction
    # ==================================================================

    def get_table_class(self) -> type[tables.Table]:
        """Resolves or dynamically generates the `django-tables2` Table class.

        Appends a `RowActionsColumn` if `row_actions` are defined on the widget.

        Raises:
            ValueError: If neither `table_class` nor `model` are configured.

        Returns:
            Configured `Table` class type.
        """
        if self.table_class is not None:
            table_class = self.table_class
        else:
            if self.model is None:
                raise ValueError(
                    f"{self.__class__.__name__} requires either "
                    "'table_class' or 'model'."
                )

            table_class = tables.table_factory(
                self.model,
                fields=self.fields,
                exclude=self.exclude,
            )

        if not self.row_actions:
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

    def build_table(self) -> tables.Table:
        """Constructs and configures the runtime `django-tables2` Table instance.

        Returns:
            Instantiated and pagination-configured `Table` object.
        """
        queryset = self.get_table_queryset()
        table_class = self.get_table_class()

        table = table_class(
            queryset,
            request=self.request,
        )

        table.widget = self

        if self.paginate:
            tables.RequestConfig(
                self.request,
                paginate={
                    "per_page": self.get_page_size(),
                },
            ).configure(table)

        return table

    # ==================================================================
    # Pagination Logic
    # ==================================================================

    def get_page_size_options(self) -> tuple[int, ...]:
        return tuple(
            size
            for size in self.page_size_options
            if size <= self.max_page_size
        )


    def get_page_size(self) -> int:
        if self.request is None:
            return self.paginate_by

        value = self.request.GET.get(self.page_size_parameter)

        if not value:
            return self.paginate_by

        try:
            size = int(value)
        except (TypeError, ValueError):
            return self.paginate_by

        if size not in self.get_page_size_options():
            return self.paginate_by

        return size

    def get_page_context(self) -> PageContext | None:
        """Generates structured pagination metadata and navigation links.

        Returns:
            `PageContext` object containing page link details, or `None` if disabled.
        """
        if not self.paginate:
            return None

        page = self.table.page
        paginator = self.table.paginator
        navigation = self.navigation

        return PageContext(
            number=page.number,
            total=paginator.num_pages,
            has_previous=page.has_previous(),
            has_next=page.has_next(),
            previous=(
                navigation.page(page.previous_page_number())
                if page.has_previous()
                else None
            ),
            next=(
                navigation.page(page.next_page_number())
                if page.has_next()
                else None
            ),
            first=(
                navigation.page(1)
                if page.number > 1
                else None
            ),
            last=(
                navigation.page(paginator.num_pages)
                if page.number < paginator.num_pages
                else None
            ),
            pages=tuple(
                (
                    number,
                    navigation.page(number),
                    number == page.number,
                )
                for number in paginator.page_range
            ),
        )

    def get_context_menu_actions(self) -> Actions:
        """
        Return the actions displayed by the static row context menu.

        By default the context menu uses row_actions.
        """
        return self.context_menu_actions or self.row_actions

    def get_table_actions(self) -> tuple[BoundAction, ...]:
        """Evaluates and binds globally visible table actions.

        Returns:
            Tuple of visible `BoundAction` instances for the table toolbar.
        """
        context = ActionContext(
            widget=self,
            request=self.request,
            data=self.get_data(),
        )

        return tuple(
            self.bind_action(action, context)
            for action in self.actions
            if action.visible(context)
        )

    def get_row_actions(self, obj: Any) -> tuple[BoundAction, ...]:
        """Evaluates and binds row-level actions for a specific model instance.

        Args:
            obj: The row data/model instance.

        Returns:
            Tuple of visible `BoundAction` instances for the row.
        """
        context = ActionContext(
            widget=self,
            request=self.request,
            object=obj,
            objects=(obj,),
            data=self.get_data(),
        )

        return tuple(
            self.bind_action(action, context)
            for action in self.row_actions
            if action.visible(context)
        )

    def get_bulk_actions(self) -> tuple[BoundAction, ...]:
        """Evaluates and binds bulk batch actions against selected records.

        Returns:
            Tuple of visible `BoundAction` instances for bulk operations.
        """
        context = ActionContext(
            widget=self,
            request=self.request,
            objects=self.get_objects(),
            data=self.get_data(),
        )

        return tuple(
            self.bind_action(action, context)
            for action in self.bulk_actions
            if action.visible(context)
        )

    def get_row_context_actions(self, obj):
        return tuple(
            action
            for action in self.get_row_actions(obj)
        )

    # ==================================================================
    # Rendering Context
    # ==================================================================

    def get_context(self) -> dict[str, Any]:
        """Assembles template evaluation context variables for widget rendering.

        Returns:
            Dictionary containing table state, actions, search terms, and IDs.
        """
        context = super().get_context()

        context.update(
            table=self.table,
            filterset=self.filterset,
            search_term=self.get_search_term(),
            search_parameter=self.search_parameter,
            search_enabled=bool(self.search_fields),
            table_actions=self.get_table_actions(),
            bulk_actions=self.get_bulk_actions(),
            table_id=self.table_id,
            content_id=self.content_id,
            selection_id=self.selection_id,
            table_url=self.endpoint,
            navigation=self.navigation,
            page=self.get_page_context(),
            empty_message=self.empty_message,
            htmx_target=self.htmx_target,
            htmx_indicator=self.htmx_indicator,
            selectable=self.selectable,
            selection_parameter=self.selection_parameter,
            toolbar=self.toolbar,
            show_search=self.show_search,
            show_filters=self.show_filters,
            show_header=self.show_header,
            show_footer=self.show_footer,
            context_menu_enabled=(
                self.context_menu
                and bool(self.get_context_menu_actions())
            ),
            context_menu_id=self.context_menu_id,
            context_menu_actions=self.get_context_menu_actions(),
            page_size=self.get_page_size(),
            page_size_options=self.get_page_size_options(),
            page_size_parameter=self.page_size_parameter,
            page_size_id=self.page_size_id,
        )

        return context