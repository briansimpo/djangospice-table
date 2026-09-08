from __future__ import annotations

from typing import Any

from django.http import Http404, HttpRequest, JsonResponse
from django.views import View

from djangospice_widget.resolver import WidgetResolver

from .datatable import DataTable


class DataTableView(View):
    """
    API endpoint for dynamically resolving and returning DataTable
    definitions.

    The table is resolved through the framework WidgetRegistry using the
    ``app_name`` and ``name`` URL parameters.
    """

    def get(self, request: HttpRequest, app_name: str, name: str, **kwargs: Any) -> JsonResponse:
        try:
            table_cls = WidgetResolver.resolve(
                app_name,
                name,
                expected_type=DataTable,
            )
        except LookupError as exc:
            raise Http404(str(exc)) from exc
        except TypeError as exc:
            raise Http404(str(exc)) from exc

        table_kwargs = {
            **request.GET.dict(),
            **kwargs,
        }

        table = table_cls(
            request=request,
            **table_kwargs,
        )

        return JsonResponse(
            table.get_definition(),
        )