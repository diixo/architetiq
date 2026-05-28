
from django.urls import path
from . import views

app_name = "app_main"

urlpatterns = [
    path("api/model/", views.api_model, name="api_model"),
    path("api/diagram/<str:view_id>/", views.api_diagram, name="api_diagram"),
    path("upload/", views.upload_model, name="upload_model"),
    path("", views.spa, name="spa"),
]
