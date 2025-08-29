from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Администратор"
        REGISTRAR = "REG", "Регистратор"
        DOCTOR = "DOC", "Врач"
        NURSE = "NUR", "Медсестра"
        PHARMACIST = "PHARM", "Провизор"
        LAB = "LAB", "Лаборант"
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.REGISTRAR)
    def __str__(self):
        return self.get_full_name() or self.username

    def is_clinician(self):
        return self.role in {self.Role.DOCTOR, self.Role.NURSE}