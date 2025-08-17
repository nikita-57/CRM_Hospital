from django.contrib import admin
from django.contrib import admin
from .models import Patient
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    search_fields = ("last_name","first_name","document_id","insurance_number")
    list_display = ("last_name","first_name","birth_date","phone","insurance_number","created_at")