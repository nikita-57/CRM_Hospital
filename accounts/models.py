from django.contrib.auth.models import AbstractUser
from django.db import models

DEPARTMENTS = [
    ("cardiology", "Кардиология"),
    ("therapy", "Терапия"),
    ("psychiatry", "Психиатрия"),
    ("neurology", "Неврология"),
]

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Администратор"
        REGISTRAR = "REG", "Регистратор"
        DOCTOR = "DOC", "Врач"
        NURSE = "NUR", "Медсестра"
        PHARMACIST = "PHARM", "Провизор"
        LAB = "LAB", "Лаборант"
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.REGISTRAR)
    department = models.CharField(
        "Отделение",
        max_length=20,
        choices=DEPARTMENTS,
        blank=True,
        null=True,
        help_text="Обязательно для регистраторов, врачей и медсестер"
    )
    def __str__(self):
        return self.get_full_name() or self.username

    def is_clinician(self):
        return self.role in {self.Role.DOCTOR, self.Role.NURSE}