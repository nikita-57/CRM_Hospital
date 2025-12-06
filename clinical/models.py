from django.db import models
from django.conf import settings
from patients.models import Patient
from django.contrib.auth import get_user_model
class Encounter(models.Model):
    class Status(models.TextChoices):
        PLANNED="PLANNED","Запланирован"
        INPROGRESS="INPROGRESS","В процессе"
        FINISHED="FINISHED","Завершен"
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="encounters")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="encounters")
    started_at = models.DateTimeField(verbose_name="Начало визита")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание визита")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Причина визита")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED, verbose_name="Статус")
    class Meta:
        verbose_name = "Визит"
        verbose_name_plural = "Визиты"
        ordering = ["-started_at"]

    def __str__(self):
        started = self.started_at.strftime("%Y-%m-%d %H:%M") if self.started_at else "не начат"
        status = self.get_status_display()
        reason = self.reason if self.reason else "без причины"
        return f"Визит {self.id} ({started}, {status}) - {self.patient}"
        
        

class Note(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

class Diagnosis(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="diagnoses")
    code = models.CharField(max_length=20)      # например, ICD-10
    description = models.CharField(max_length=255)

class Prescription(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="prescriptions")
    medication = models.CharField(max_length=120)
    dosage = models.CharField(max_length=120)           # 500 mg
    frequency = models.CharField(max_length=120)        # 2 раза в день
    duration_days = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Attachment(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)

class PatientInteraction(models.Model):
    ACTIONS = [
        ("visit_created", "Создан визит"),
        ("visit_closed", "Закрыт визит"),
        ("note_add", "Добавлена заметка"),
        ("rx_add", "Назначение лекарства"),
        ("patient_update", "Обновлена информация о пациенте"),
        ("facility_update", "Обновлена информация о месте размещения"),
    ]
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="interactions")
    User = get_user_model()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    action = models.CharField(max_length=50, choices=ACTIONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.get_action_display()} - {self.patient} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"