from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q

class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles: set[str] = set()
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (not self.allowed_roles or u.role in self.allowed_roles)
    
class PatientFilterMixin:
    def apply_filters(self, qs):
        # Фильтр по статусу активный/удалённый
        status = self.request.GET.get("status", "active")
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "deleted":
            qs = qs.filter(is_active=False)

        # Фильтр по возрасту (если надо)
        patient_type = self.request.GET.get("type")
        if patient_type == "adult":
            qs = qs.filter(patient_type="adult")
        elif patient_type == "child":
            qs = qs.filter(patient_type="child")

        return qs