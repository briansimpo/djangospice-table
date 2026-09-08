# djangospice_table

Interactive server-side table widget for Django applications.

`djangospice_table` provides a request-aware table component for Django applications. It builds on `django-tables2` and `django-filter` to provide a consistent table experience with search, filtering, pagination, configurable page limits, selection, actions, and HTMX support.

---

## Features

* Django model-backed tables
* Search
* Filtering
* Pagination
* Page limits
* Row selection
* Table actions
* Row actions
* Bulk actions
* Context menus
* HTMX support

---

## Installation

```bash
pip install djangospice-table
```

Add the package to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "djangospice_table",
]
```

---

## Basic Usage

Create a table widget from a Django model:

```python
from djangospice_table import TableWidget


class StudentTableWidget(TableWidget):
    title = "Students"
    model = Student

    fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
    )
```

Render the widget:

```django
{% render_widget "students.student-table" %}
```

---

## Model

Set `model` to the Django model represented by the table:

```python
class StudentTableWidget(TableWidget):
    model = Student
```

---

## Fields

Specify the fields displayed by the table:

```python
class StudentTableWidget(TableWidget):
    model = Student

    fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
    )
```

Fields can also be excluded:

```python
class StudentTableWidget(TableWidget):
    model = Student

    exclude = (
        "created_at",
        "updated_at",
    )
```

---

## Custom Table

A custom `django-tables2` table class can be supplied when more control over the table definition is required:

```python
import django_tables2 as tables


class StudentTable(tables.Table):
    student_number = tables.Column(
        verbose_name="Student Number"
    )

    name = tables.Column(
        accessor="full_name"
    )


class StudentTableWidget(TableWidget):
    model = Student
    table_class = StudentTable
```

---

## Querysets

Customize the records displayed by the table:

```python
class StudentTableWidget(TableWidget):
    model = Student

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(active=True)
        )
```

This can be used for application-specific filtering, access rules, or other queryset requirements.

---

## Search

Configure searchable fields:

```python
class StudentTableWidget(TableWidget):
    model = Student

    search_fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
    )
```

The default search parameter is `q`.

It can be customized:

```python
class StudentTableWidget(TableWidget):
    search_parameter = "search"
```

Example:

```text
/students/?search=john
```

---

## Filters

Use a `django-filter` filterset:

```python
import django_filters


class StudentFilter(django_filters.FilterSet):
    active = django_filters.BooleanFilter()


class StudentTableWidget(TableWidget):
    model = Student
    filterset_class = StudentFilter
```

Filters work alongside search, pagination, and other table state.

---

## Pagination

Pagination is enabled by default:

```python
class StudentTableWidget(TableWidget):
    model = Student

    paginate = True
    paginate_by = 20
```

Disable pagination when required:

```python
class StudentTableWidget(TableWidget):
    model = Student
    paginate = False
```

---

## Page Limits

Tables provide configurable page-size options.

The default options are:

```text
10
20
50
100
500
```

The default page size is `20`.

Customize the available options:

```python
class StudentTableWidget(TableWidget):
    page_size_options = (
        10,
        20,
        50,
        100,
        500,
    )
```

Set a different default:

```python
class StudentTableWidget(TableWidget):
    paginate_by = 50
```

Limit the maximum page size:

```python
class StudentTableWidget(TableWidget):
    max_page_size = 100
```

The resulting available options will not exceed the configured maximum.

---

## Limit Parameter

The default page-size parameter is:

```text
page_size
```

It can be changed to `limit`:

```python
class StudentTableWidget(TableWidget):
    page_size_parameter = "limit"
```

This allows URLs such as:

```text
/students/?limit=100
```

The page limit works together with the table's existing search, filter, and pagination state.

---

## Row Selection

Enable row selection:

```python
class StudentTableWidget(TableWidget):
    model = Student
    selectable = True
```

Customize the selection parameter:

```python
class StudentTableWidget(TableWidget):
    selectable = True
    selection_parameter = "students"
```

---

## Actions

Table-level actions can be declared with `Actions`:

```python
from djangospice_table import Actions


class StudentTableWidget(TableWidget):
    actions = Actions(
        ExportStudentsAction,
        ImportStudentsAction,
    )
```

---

## Row Actions

Actions can be displayed for individual rows:

```python
class StudentTableWidget(TableWidget):
    model = Student

    row_actions = Actions(
        ViewStudentAction,
        EditStudentAction,
        DeleteStudentAction,
    )
```

Row actions operate on the corresponding table record.

---

## Bulk Actions

Bulk actions operate on selected records:

```python
class StudentTableWidget(TableWidget):
    model = Student
    selectable = True

    bulk_actions = Actions(
        ActivateStudentsAction,
        DeactivateStudentsAction,
        DeleteStudentsAction,
    )
```

---

## Context Menus

Enable a context menu for table rows:

```python
class StudentTableWidget(TableWidget):
    model = Student

    row_actions = Actions(
        ViewStudentAction,
        EditStudentAction,
        DeleteStudentAction,
    )

    context_menu = True
```

A dedicated set of context-menu actions can also be configured:

```python
class StudentTableWidget(TableWidget):
    context_menu_actions = Actions(
        ViewStudentAction,
        EditStudentAction,
    )
```

---

## HTMX

`djangospice_table` is designed to work naturally with HTMX.

Tables can be refreshed or interacted with without requiring a full page reload.

Typical table interactions include:

* search
* filtering
* pagination
* changing the page limit
* row actions
* bulk actions
* context-menu actions

---

## Composable UI

The table UI is designed to be composed from reusable pieces.

Common table components include:

* toolbar
* search
* filters
* actions
* bulk actions
* table
* row actions
* context menu
* empty state
* pagination
* page-size selector

This allows applications to build different table layouts without duplicating table behavior.

---

## Complete Example

```python
from djangospice_table import Actions, TableWidget


class StudentTableWidget(TableWidget):
    title = "Students"

    model = Student

    fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
    )

    search_fields = (
        "student_number",
        "first_name",
        "last_name",
        "email",
    )

    filterset_class = StudentFilter

    paginate = True
    paginate_by = 20

    page_size_options = (
        10,
        20,
        50,
        100,
        500,
    )

    max_page_size = 500

    selectable = True

    actions = Actions(
        ExportStudentsAction,
    )

    row_actions = Actions(
        ViewStudentAction,
        EditStudentAction,
        DeleteStudentAction,
    )

    bulk_actions = Actions(
        ActivateStudentsAction,
        DeactivateStudentsAction,
    )

    context_menu = True
```

---

## Requirements

* Python 3.12+
* Django 5.0+
* django-tables2
* django-filter

HTMX is required for HTMX-based interactions.

---

## License

This package is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.

