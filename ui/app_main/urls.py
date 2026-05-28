
from django.urls import path
from . import views

app_name = "app_main"

urlpatterns = [
    path("api/model/",        views.api_model,        name="api_model"),
    path("api/model/new/",    views.api_model_new,    name="api_model_new"),
    path("api/model/save/",   views.api_model_save,   name="api_model_save"),
    path("api/model/export/", views.api_model_export, name="api_model_export"),
    path("api/diagram/<str:view_id>/", views.api_diagram, name="api_diagram"),
    path("upload/",           views.upload_model,     name="upload_model"),
    path("",                  views.spa,              name="spa"),
]
