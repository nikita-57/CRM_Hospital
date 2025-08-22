# web/forms.py
from django import forms
from datetime import date
from patients.models import Patient
from clinical.models import Encounter, Note, Prescription

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "last_name", "first_name", "middle_name",
            "birth_date", "gender",
            "phone", "email",
            "document_id", "insurance_number",
            "address", "emergency_contact",
        ]
        widgets = {
            "birth_date": forms.DateInput(
                attrs={
                    "type": "text",
                    "class": "form-control js-date",
                    "placeholder": "ГГГГ-ММ-ДД",
                    "data-max": date.today().isoformat(),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control js-phone",
                    "placeholder": "+7 (___) ___-__-__",
                    "autocomplete": "tel",
                    "inputmode": "tel",
                }
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "name@example.com"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "document_id": forms.TextInput(attrs={"class": "form-control"}),
            "insurance_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget.attrs.setdefault("data-max", date.today().isoformat())

class EncounterForm(forms.ModelForm):
    class Meta:
        model = Encounter
        fields = ["patient", "doctor", "started_at", "reason", "status"]
        widgets = {
            "started_at": forms.TextInput(
                attrs={
                    "type": "text",
                    "class": "form-control js-datetime",
                    "placeholder": "ГГГГ-ММ-ДД ЧЧ:ММ",
                }
            ),
            "patient": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["started_at"].input_formats = ["%Y-%m-%d %H:%M"]

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["encounter", "text"]
        labels = {
            "encounter": "Визит",
            "text": "Текст заметки",
        }
        widgets = {
            "encounter": forms.Select(attrs={"class": "form-select"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Текст заметки"}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["encounter", "medication", "dosage", "frequency", "duration_days", "notes"]
        labels = {
            "encounter": "Визит",
            "medication": "Лекарство",
            "dosage": "Дозировка",
            "frequency": "Частота",
            "duration_days": "Продолжительность (дней)",
            "notes": "Дополнительные заметки",
        }
        widgets = {
            "encounter": forms.Select(attrs={"class": "form-select"}),
            "medication": forms.TextInput(attrs={"class": "form-control"}),
            "dosage": forms.TextInput(attrs={"class": "form-control"}),
            "frequency": forms.TextInput(attrs={"class": "form-control", "placeholder": "2 раза в день"}),
            "duration_days": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
