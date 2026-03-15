from django.db import models
from django.conf import settings

DEPARTMENT_CHOICES = [
    ("cardiology", "Кардиология"),
    ("therapy", "Терапия"),
    ("psychiatry", "Психиатрия"),
    ("neurology", "Неврология"),
]


class Event(models.Model):
    """Мероприятие в плане работы"""
    EVENT_TYPES = [
        ("meeting", "Совещание"),
        ("training", "Обучение"),
        ("inspection", "Проверка"),
        ("report", "Отчёт"),
        ("other", "Другое"),
    ]

    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    event_type = models.CharField(
        "Тип мероприятия",
        max_length=20,
        choices=EVENT_TYPES,
        default="other",
    )
    event_date = models.DateField("Дата проведения")
    event_time = models.TimeField("Время начала", blank=True, null=True)
    department = models.CharField(
        "Отделение",
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True,
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ответственный",
        related_name="events",
    )
    is_completed = models.BooleanField("Выполнено", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Создал",
        related_name="created_events",
    )

    def __str__(self):
        return f"{self.title} ({self.event_date.strftime('%d.%m.%Y')})"

    class Meta:
        ordering = ["-event_date", "-event_time"]
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
