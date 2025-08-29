from django.db import models

class Patient(models.Model):
    GENDER_CHOICES = [("M","Муж"),("F","Жен"),("O","Др.")]
    first_name = models.CharField('Имя', max_length=120)
    last_name  = models.CharField('Фамилия', max_length=120)
    middle_name = models.CharField("Отчество", max_length=120, blank=True)
    birth_date = models.DateField('Дата рождения')
    gender = models.CharField( "Пол", max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    document_id = models.CharField('Личный номер', max_length=64, blank= True)  #личный номер
    insurance_number = models.CharField("Полис", max_length=64, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    emergency_contact = models.CharField("Контакт для связи", max_length=255, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["last_name","first_name","birth_date"]

    def __str__(self):
        fio = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return f"{fio} ({self.birth_date})"
