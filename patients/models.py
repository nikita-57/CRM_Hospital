from django.db import models
from datetime import date

class Patient(models.Model):
    GENDER_CHOICES = [
        ("M", "Муж"),
        ("F", "Жен"),
    ]
    PATIENT_TYPE_CHOICES = [
        ("adult", "Взрослый"),
        ("child", "Ребёнок"),
    ]
    first_name = models.CharField("Имя", max_length=120)
    last_name = models.CharField("Фамилия", max_length=120)
    middle_name = models.CharField("Отчество", max_length=120, blank=True)

    birth_date = models.DateField("Дата рождения")
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES)
    patient_type = models.CharField(
        "Тип пациента",
        max_length=10,
        choices=PATIENT_TYPE_CHOICES,
        default="adult",
    )
    phone = models.CharField("Телефон", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    document_id = models.CharField("Личный номер", max_length=64, blank=True)
    insurance_number = models.CharField("Полис", max_length=64, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    emergency_contact = models.CharField("Контакт для связи", max_length=255, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    @property
    def age(self):
        """Возраст пациента в полных годах"""
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def is_child(self):
        """True, если пациент младше 18 лет"""
        return self.age is not None and self.age < 18

    def __str__(self):
        fio = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        status = '' if self.is_active else ' [УДАЛЕН]'
        return f"{fio} ({self.birth_date.strftime('%d.%m.%Y')})"

    class Meta:
        ordering = ["last_name", "first_name", "birth_date"]
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"
