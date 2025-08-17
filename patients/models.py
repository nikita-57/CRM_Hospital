from django.db import models

class Patient(models.Model):
    GENDER_CHOICES = [("M","Муж"),("F","Жен"),("O","Др.")]
    first_name = models.CharField(max_length=120)
    last_name  = models.CharField(max_length=120)
    middle_name = models.CharField(max_length=120, blank=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    document_id = models.CharField(max_length=64, blank=True)  # паспорт/полис
    insurance_number = models.CharField(max_length=64, blank=True)
    address = models.CharField(max_length=255, blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name","first_name","birth_date"]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.birth_date})"