from django.urls import path
from djangospice_widget.conf import APP_NAME_URL_KEY, MODEL_NAME_URL_KEY
from .apps import namespace
from .views import DataTableView


urlpatterns = [
    path(
        f"datatable/{APP_NAME_URL_KEY}>/{MODEL_NAME_URL_KEY}/", 
        DataTableView.as_view(),
        name=namespace,
    ),

]