from django.contrib import admin

from .models import Encounter, Note, Diagnosis, Prescription, Attachment
admin.site.register([Encounter, Note, Diagnosis, Prescription, Attachment])