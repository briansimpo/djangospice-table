from __future__ import annotations

from django import template
from django.templatetags.static import static
from djangospice_lookup.apps import namespace

register = template.Library()


TABLE_CSS = f"{namespace}/table.css"
TABLE_JS = f"{namespace}/table.js"


def _table_css() -> str:
    return (
        f'<link rel="stylesheet" href="{static(TABLE_CSS)}">'
    )


def _table_js() -> str:
    return (
        f'<script src="{static(TABLE_JS)}" defer></script>'
    )


@register.simple_tag
def djangospice_table_css() -> str:
    """Render the DjangoSpice Table stylesheet."""
    return _table_css()


@register.simple_tag
def djangospice_lookup_js() -> str:
    """Render the DjangoSpice Table JavaScript."""
    return _table_js()


@register.simple_tag
def djangospice_lookup_assets() -> str:
    """Render all DjangoSpice Table assets."""
    return "\n".join(
        (
            _table_css(),
            _table_js(),
        )
    )