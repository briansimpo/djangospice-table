# djangospice_table

**Reusable, composable, server-side data tables for Django.**

`djangospice-table` provides declarative data table widgets for Django applications, built on top of `django-tables2`, with integrated filtering, searching, pagination, actions, HTMX-compatible rendering, and optional dynamic JavaScript rendering.

---

## Features

- Server-side data table rendering
- Built on `django-tables2`
- Declarative table widgets
- Automatic table generation from Django models
- Custom `django-tables2` table classes
- Field inclusion and exclusion
- `django-filter` integration
- Server-side search
- Server-side sorting
- Server-side pagination
- Configurable page-size options
- Table, row, and bulk actions
- Selectable rows
- Context-menu support
- DataTable API
- Declarative JSON table definitions
- Remote lookup-compatible filters
- HTMX-compatible rendering
- Automatic JavaScript table discovery
- Django template tags

---

## Installation

```bash
pip install djangospice-table
```

Add the application to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...

    "djangospice_table",
]
```

---

## Basic Usage

A data table can be generated directly from a Django model:

```python
from djangospice_table import TableWidget


class StudentTable(TableWidget):
    model = Student
```

You can restrict the displayed fields:

```python
class StudentTable(TableWidget):
    model = Student

    fields = (
        "student_number",
        "name",
        "program",
    )
```

Or exclude fields:

```python
class StudentTable(TableWidget):
    model = Student

    exclude = (
        "created_at",
        "updated_at",
    )
```

---

## Custom Tables

For more control, provide a `django-tables2` table class:

```python
import django_tables2 as tables

from djangospice_table import TableWidget


class StudentTableDefinition(tables.Table):
    student_number = tables.Column(
        verbose_name="Student Number",
    )

    name = tables.Column()

    class Meta:
        model = Student
        fields = (
            "student_number",
            "name",
            "program",
        )


class StudentTable(TableWidget):
    table_class = StudentTableDefinition
```

This allows you to use the `django-tables2` table API for custom columns and table behavior.

---

## Querysets

Customize the queryset using the normal Django queryset API:

```python
class StudentTable(TableWidget):
    model = Student

    def get_queryset(self):
        return (
            Student.objects
            .select_related("program")
            .filter(active=True)
        )
```

---

## Searching

Enable server-side search with `search_fields`:

```python
class StudentTable(TableWidget):
    model = Student

    search_fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
    )
```

The default search parameter is:

```text
q
```

For example:

```text
/students/?q=Brian
```

Search is performed server-side, making it suitable for large datasets.

---

## Filtering

`TableWidget` integrates with `django-filter`:

```python
import django_filters

from djangospice_table import TableWidget


class StudentFilter(django_filters.FilterSet):
    program = django_filters.ModelChoiceFilter(
        queryset=Program.objects.all(),
    )

    class Meta:
        model = Student
        fields = (
            "program",
        )


class StudentTable(TableWidget):
    model = Student
    filterset_class = StudentFilter
```

Filters are applied server-side.

For large filter datasets, use remote lookup-backed filters so that large option sets do not need to be embedded in the table response.

---

## Pagination

Pagination is enabled by default:

```python
class StudentTable(TableWidget):
    model = Student

    paginate_by = 20
```

Configure page-size options:

```python
class StudentTable(TableWidget):
    model = Student

    paginate_by = 20

    page_size_options = (
        10,
        20,
        50,
        100,
        500,
    )
```

The default query parameters are:

```text
page
page_size
```

Example:

```text
/students/?page=2&page_size=50
```

---

## Row Selection

Enable row selection:

```python
class StudentTable(TableWidget):
    model = Student

    selectable = True
```

Selected records are submitted using:

```text
selected_ids
```

---

## Actions

`TableWidget` uses the DjangoSpice action system for table operations. Actions are declared as action collections and are evaluated against an `ActionContext` before they are exposed to the user.

Three action collections are available:

- `actions` — global actions for the table
- `row_actions` — actions for an individual row
- `bulk_actions` — actions for a selected set of rows

The collections contain DjangoSpice `Action` objects, rather than action names or strings.

### Table Actions

Table actions are global actions displayed by the table toolbar. They operate in the context of the table and do not have a specific object associated with them.

```python
from djangospice_table import TableWidget
from djangospice_widget.actions import Action, Actions


class StudentTable(TableWidget):
    model = Student

    actions = Actions(
        Action(
            name="export",
            label="Export",
        ),
    )
```

A table action receives an `ActionContext` containing the widget, request, and widget data.

### Row Actions

Row actions operate on a specific record. They are rendered for each row, typically through the table's row-action column.

```python
class StudentTable(TableWidget):
    model = Student

    row_actions = Actions(
        Action(
            name="edit",
            label="Edit",
        ),
        Action(
            name="delete",
            label="Delete",
        ),
    )
```

For a row action, the `ActionContext` contains:

- `widget` — the current `TableWidget`
- `request` — the current Django request
- `object` — the row's object
- `objects` — a tuple containing that object
- `data` — the widget data

This allows an action to work directly with the record it is being invoked against.

### Bulk Actions

Bulk actions operate on multiple selected records.

Enable selection and define the bulk actions:

```python
class StudentTable(TableWidget):
    model = Student

    selectable = True

    bulk_actions = Actions(
        Action(
            name="activate",
            label="Activate",
        ),
        Action(
            name="deactivate",
            label="Deactivate",
        ),
    )
```

For a bulk action, the `ActionContext` contains:

- `widget` — the current `TableWidget`
- `request` — the current Django request
- `objects` — the selected objects
- `data` — the widget data

The selected objects are resolved by the table widget before the action is bound.

### Action Context

The action context is different depending on where the action is used.

A table action receives table-level context:

```python
ActionContext(
    widget=table,
    request=request,
    data=table.get_data(),
)
```

A row action receives the current object:

```python
ActionContext(
    widget=table,
    request=request,
    object=student,
    objects=(student,),
    data=table.get_data(),
)
```

A bulk action receives the selected objects:

```python
ActionContext(
    widget=table,
    request=request,
    objects=selected_students,
    data=table.get_data(),
)
```

This gives actions a consistent interface while preserving the distinction between table, row, and bulk operations.

### Action Visibility

Actions are evaluated against their context before being exposed.

For example, a row action can determine whether it should be visible for a particular record:

```python
class StudentTable(TableWidget):
    model = Student

    row_actions = Actions(
        Action(
            name="activate",
            label="Activate",
            visible=lambda context: not context.object.is_active,
        ),
        Action(
            name="deactivate",
            label="Deactivate",
            visible=lambda context: context.object.is_active,
        ),
    )
```

The table widget binds each visible action to its `ActionContext`, producing a `BoundAction`.

This means templates and table columns work with actions that are already associated with their execution context rather than raw, unbound action definitions.

### Context Menu Actions

A table can also define actions for its row context menu.

```python
class StudentTable(TableWidget):
    model = Student

    row_actions = Actions(
        Action(
            name="view",
            label="View",
        ),
        Action(
            name="edit",
            label="Edit",
        ),
    )

    context_menu_actions = Actions(
        Action(
            name="view",
            label="View",
        ),
        Action(
            name="edit",
            label="Edit",
        ),
    )
```

When `context_menu_actions` is not explicitly defined, the table uses `row_actions` for the row context menu.

### Complete Actions Example

A table can combine all three action scopes:

```python
from djangospice_table import TableWidget
from djangospice_widget.actions import Action, Actions


class StudentTable(TableWidget):
    model = Student

    actions = Actions(
        Action(
            name="export",
            label="Export",
        ),
    )

    row_actions = Actions(
        Action(
            name="view",
            label="View",
        ),
        Action(
            name="edit",
            label="Edit",
        ),
        Action(
            name="delete",
            label="Delete",
        ),
    )

    bulk_actions = Actions(
        Action(
            name="activate",
            label="Activate",
        ),
        Action(
            name="deactivate",
            label="Deactivate",
        ),
    )

    selectable = True
```

The same action architecture is used by the table's server-rendered UI and its DataTable representation.

## Context Menus

Context-menu support is available for table rows and actions.

Load the context-menu asset with:

```django
{% load table %}

{% djangospice_table_contextmenu_js %}
```

---

# DataTable

`DataTable` provides client-side rendering while retaining server-side data processing.

```python
from djangospice_table import DataTable


class StudentTable(DataTable):
    model = Student

    fields = (
        "student_number",
        "name",
        "program",
    )

    search_fields = (
        "student_number",
        "name",
    )

    paginate_by = 20
```

`DataTable` provides the same table capabilities as `TableWidget` while additionally exposing the table through the DataTable API and JavaScript client.

---

## Rendering

DataTables are rendered through the standard DjangoSpice widget system:

```django
{% load djangospice_widget %}

{% render_widget "students" %}
```

The initial response contains a lightweight DataTable placeholder.

The DataTable JavaScript client automatically discovers the placeholder and loads the table data from its API endpoint.

No manual JavaScript initialization is required.

---

## DataTable API

DataTables expose a JSON API endpoint.

A typical endpoint is:

```text
/api/tables/<app_name>/<name>/
```

For example:

```text
/api/tables/academic/students/
```

The endpoint returns the current table definition.

---

## DataTable Response

A DataTable response contains the table configuration, columns, rows, filters, search state, sorting, pagination, and actions.

```json
{
    "type": "table",
    "id": "students",
    "configuration": {
        "selectable": true,
        "searchable": true,
        "sortable": true,
        "filterable": true,
        "pagination": true,
        "page_size": 20,
        "page_size_options": [10, 20, 50, 100, 500]
    },
    "columns": [
        {
            "name": "student_number",
            "label": "Student Number",
            "orderable": true
        },
        {
            "name": "name",
            "label": "Name",
            "orderable": true
        }
    ],
    "rows": [],
    "filters": [],
    "search": {},
    "sorting": {},
    "pagination": {},
    "actions": {
        "table": [],
        "row": [],
        "bulk": []
    }
}
```

---

## Remote Lookups

Large filter datasets can use remote lookup sources instead of embedding all available choices in the table response.

Example:

```json
{
    "name": "program",
    "type": "lookup",
    "label": "Program",
    "multiple": true,
    "source": {
        "type": "remote",
        "endpoint": "/lookups/programs/",
        "searchable": true,
        "page_size": 20
    }
}
```

The lookup endpoint independently provides its available options and pagination.

This keeps DataTable responses lightweight even when filters contain large datasets.

---

## JavaScript

The package provides:

```text
datatable.js
```

The JavaScript client automatically discovers DataTable placeholders.

It handles:

- Initial table loading
- Rendering
- Searching
- Filtering
- Sorting
- Pagination
- Page-size changes
- Row selection
- Table actions
- Bulk actions
- Dynamic updates
- HTMX-inserted tables

No explicit initialization is required when using the standard widget rendering flow.

---

## Assets

The package provides three frontend assets:

```text
table.css
datatable.js
contextmenu.js
```

Load the stylesheet:

```django
{% load table %}

{% djangospice_table_css %}
```

Load the DataTable JavaScript:

```django
{% djangospice_table_js %}
```

Load the context-menu JavaScript:

```django
{% djangospice_table_contextmenu_js %}
```

Or load all table assets:

```django
{% djangospice_table_assets %}
```

---

## HTMX

DataTables support tables rendered inside HTMX requests and dynamically inserted fragments.

Newly inserted DataTable placeholders are automatically discovered by the JavaScript client.

This allows DataTables to be used in:

- Dialogs
- Tabs
- Drawers
- Partial page updates
- Dashboard widgets
- Dynamically loaded content

---

## Complete Example

```python
from djangospice_table import DataTable


class StudentTable(DataTable):
    model = Student

    fields = (
        "student_number",
        "name",
        "program",
        "study_mode",
        "status",
    )

    search_fields = (
        "student_number",
        "name",
        "email",
    )

    paginate = True
    paginate_by = 20

    page_size_options = (
        10,
        20,
        50,
        100,
        500,
    )

    selectable = True

    show_search = True
    show_filters = True
```

Render it through the standard widget system:

```django
{% load djangospice_widget %}

{% render_widget "students" %}
```

Load the assets once in the page:

```django
{% load table %}

{% djangospice_table_assets %}
```

The DataTable is then discovered and initialized automatically.

---

## Requirements

- Python
- Django
- `django-tables2`
- `django-filter`
- `djangospice-framework`
- `djangospice-widget`

---

## License

This package is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.
