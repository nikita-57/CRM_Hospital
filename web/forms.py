# web/forms.py
from django import forms
from datetime import date
from patients.models import Patient
from clinical.models import Encounter, Note, Prescription
from accounts.models import User

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'last_name', 'first_name', 'middle_name', 
            'birth_date', 'gender', 'patient_type', 
            'facility', 'department', 'doctor',
            'phone', 'employer', 'callsign', 'insurance_number', 'document_id', 'address'
        ]
        widgets = {
            "birth_date": forms.DateInput(
                attrs={
                    "type": "text",
                    "class": "form-control js-date",
                    "placeholder": "ГГГГ-ММ-ДД",
                    "data-max": date.today().isoformat(),
                    "patient_type": forms.Select(attrs={"class": "form-select"}),
                }
            ),
            "patient_type": forms.Select(attrs={"class": "form-select"}),
            "facility": forms.Select(attrs={"class": "form-select"}),
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
            "callsign": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget.attrs.setdefault("data-max", date.today().isoformat())
        self.fields["doctor"].widget.attrs.update({"class": "form-select"})

class EncounterForm(forms.ModelForm):
    started_at = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%d %H:%M",
            attrs={
                "type": "text",
                "class": "form-control js-datetime",
                "placeholder": "ГГГГ-ММ-ДД ЧЧ:ММ",
            },
        ),
    )

    class Meta:
        model = Encounter
        fields = ["started_at", "reason", "status"]
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.TextInput(attrs={"class": "form-control", "placeholder": "Причина визита"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get('patient'):
            self.fields['patient'].widget = forms.HiddenInput()
        if self.initial.get('doctor'):
            self.fields['doctor'].widget = forms.HiddenInput()

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
