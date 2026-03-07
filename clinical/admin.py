from django.contrib import admin

from .models import Encounter, Note, Diagnosis, Prescription, Attachment, TreatmentPlanItem
admin.site.register([Encounter, Note, Diagnosis, Prescription, Attachment, TreatmentPlanItem])