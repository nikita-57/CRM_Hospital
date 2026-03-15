from django.urls import path
from .views import PlanningView

app_name = "planning"

urlpatterns = [
    path("", PlanningView.as_view(), name="list"),
]
