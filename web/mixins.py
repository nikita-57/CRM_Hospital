from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles: set[str] = set()
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (not self.allowed_roles or u.role in self.allowed_roles)