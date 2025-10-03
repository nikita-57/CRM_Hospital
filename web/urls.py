from django.urls import path
from django.contrib.auth import views as auth_views
from .views import Dashboard, PatientList, PatientCreate, PatientDetail
from .views import PatientUpdate
from .views import AdultPatientList, ChildrenPatients

app_name = "web"

urlpatterns = [
    path("", Dashboard.as_view(), name="dashboard"),
    path("patients/", PatientList.as_view(), name="patients"),
    path("patients/adults/", AdultPatientList.as_view(), name="patients_adults"),
    path("patients/children/", ChildrenPatients.as_view(), name="patients_children"),
    path("patients/create/", PatientCreate.as_view(), name="patient_create"),
    path("patients/<int:pk>/", PatientDetail.as_view(), name="patient_detail"),
    path("patients/<int:pk>/edit/", PatientUpdate.as_view(), name="patient_update"),
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
