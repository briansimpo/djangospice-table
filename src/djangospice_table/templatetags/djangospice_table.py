from __future__ import annotations

from django import template
from django.templatetags.static import static

from djangospice_table.apps import namespace


register = template.Library()


TABLE_CSS = f"{namespace}/table.css"
DATATABLE_JS = f"{namespace}/datatable.js"
CONTEXTMENU_JS = f"{namespace}/contextmenu.js"


def _table_css() -> str:
    return f'<link rel="stylesheet" href="{static(TABLE_CSS)}">'


def _datatable_js() -> str:
    return f'<script src="{static(DATATABLE_JS)}" defer></script>'


def _contextmenu_js() -> str:
    return f'<script src="{static(CONTEXTMENU_JS)}" defer></script>'


@register.simple_tag
def djangospice_table_css() -> str:
    """Render the DjangoSpice Table stylesheet."""
    return _table_css()


@register.simple_tag
def djangospice_table_js() -> str:
    """Render the DjangoSpice DataTable JavaScript."""
    return _datatable_js()


@register.simple_tag
def djangospice_table_contextmenu_js() -> str:
    """Render the DjangoSpice Table context-menu JavaScript."""
    return _contextmenu_js()


@register.simple_tag
def djangospice_table_assets() -> str:
    """Render all DjangoSpice Table assets."""
    return "\n".join(
        (
            _table_css(),
            _datatable_js(),
            _contextmenu_js(),
        )
    )