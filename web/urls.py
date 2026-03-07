from django.urls import path
from django.contrib.auth import views as auth_views
from .views import Dashboard, PatientList, PatientCreate, PatientDetail, PatientSoftDelete, PatientRestore, PatientUpdate, AdultPatientList, ChildrenPatients, StatsView
from .views import PatientCertificateView, UserCreate, UserList, UserUpdate, UserDelete, UserRestore
from . import views
app_name = "web"

urlpatterns = [
    path("", Dashboard.as_view(), name="dashboard"),
    path("patients/", PatientList.as_view(), name="patients"),
    path("patients/adults/", AdultPatientList.as_view(), name="patients_adults"),
    path("patients/children/", ChildrenPatients.as_view(), name="patients_children"),
    path("patients/create/", PatientCreate.as_view(), name="patient_create"),
    path("patients/<int:pk>/", PatientDetail.as_view(), name="patient_detail"),
    path("patients/<int:pk>/edit/", PatientUpdate.as_view(), name="patient_update"),
    path("patients/<int:pk>/delete/", PatientSoftDelete.as_view(), name="patient_delete"),
    path("patients/<int:pk>/restore/", PatientRestore.as_view(), name="patient_restore"),
    path("users/", UserList.as_view(), name="users"),
    path("users/create/", UserCreate.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", UserUpdate.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", UserDelete.as_view(), name="user_delete"),
    path("users/<int:pk>/restore/", UserRestore.as_view(), name="user_restore"),
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("stats/departments/", StatsView.as_view(), name="departments"),
    path("patients/<int:pk>/certificate/", PatientCertificateView.as_view(), name="patient_certificate"),
    path('api/get-doctors/', views.get_doctors_by_department, name='api_get_doctors'),

]