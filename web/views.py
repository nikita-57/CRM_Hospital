from django.views import View
from django.db.models.functions import TruncDate
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Prefetch, Count
from django.utils import timezone
from django.views.generic import UpdateView
from django.urls import reverse
from django.shortcuts import get_object_or_404
from .forms import PatientForm, EncounterForm, NoteForm, PrescriptionForm
from patients.models import Patient, DEPARTMENT_CHOICES, Facility
from clinical.models import Encounter, Note, Prescription
from .mixins import RoleRequiredMixin, PatientFilterMixin
from django.db.models.functions import TruncWeek, TruncMonth, TruncDay
from django.db import models
from django.views.generic import TemplateView
from django.shortcuts import redirect
from calendar import monthrange
from datetime import datetime, date, timedelta
import calendar
from clinical.utils import log_patient_interaction
from django.http import HttpResponse
from django.conf import settings
from docx import Document
from django.utils.timezone import now
import os
from accounts.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now, timedelta
from django.db.models.functions import TruncDate

class PatientList(RoleRequiredMixin, PatientFilterMixin, ListView):
    model = Patient
    template_name = "patients/list.html"
    paginate_by = 20
    allowed_roles = {"ADMIN", "REG", "DOC", "NUR"}
    context_object_name = "patients"
    

    def get_queryset(self):
        qs = super().get_queryset()

        qs = self.apply_filters(qs)
        user = self.request.user

        if user.role == "DOC":
            qs = qs.filter(department=user.department, is_active=True).distinct()

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(phone__icontains=q) |
                Q(document_id__icontains=q) |
                Q(insurance_number__icontains=q)
            )
        facility = self.request.GET.get("facility")
        if facility:
            if facility == "none":
                qs = qs.filter(facility__isnull=True)
            else:
                qs = qs.filter(facility__id=facility)
        type_filter = self.request.GET.get("type")
        if type_filter in {"adult", "child", "unknown"}:
            qs = qs.filter(patient_type=type_filter)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["facilities"] = Facility.objects.all()
        return ctx
    




class PatientCreate(RoleRequiredMixin, CreateView):
    form_class = PatientForm
    template_name = "patients/create.html"
    success_url = reverse_lazy("web:patients")
    allowed_roles = {"ADMIN", "REG"}


class PatientDetail(RoleRequiredMixin, DetailView):
    model = Patient
    template_name = "patients/detail.html"
    allowed_roles = {"ADMIN", "REG", "DOC", "NUR"}

    def get_queryset(self):
        """Врачи и медсёстры видят только пациентов своего отделения."""
        qs = super().get_queryset()
        user = self.request.user

        if user.role in {"DOC", "NUR"}:
            qs = qs.filter(department=user.department, is_active=True)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient = self.object

        # Все визиты пациента
        enc_qs = Encounter.objects.filter(patient=patient).order_by("-started_at")
        ctx["encounters"] = enc_qs

        # Форма создания визита (без patient и doctor — они будут выставлены в post)
        ctx["encounter_form"] = EncounterForm()
        ctx["interactions"] = patient.interactions.all().order_by("-created_at")
        # Формы заметки и назначения
        default_enc_id = enc_qs[0].id if enc_qs else None

        note_form = NoteForm(initial={"encounter": default_enc_id})
        note_form.fields["encounter"].queryset = enc_qs
        ctx["note_form"] = note_form

        rx_form = PrescriptionForm(initial={"encounter": default_enc_id})
        rx_form.fields["encounter"].queryset = enc_qs
        ctx["rx_form"] = rx_form

        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")

        # --- Создание визита ---
        if action == "add_encounter":
            if request.user.role not in {"ADMIN", "DOC", "NUR", "REG"}:
                messages.error(request, "Нет прав на создание визита.")
                return redirect(self.request.path)

            form = EncounterForm(request.POST)
            if form.is_valid():
                encounter = form.save(commit=False)
                encounter.patient = self.object      # Привязываем к текущему пациенту
                encounter.doctor = request.user      # Автор визита – тот, кто создал
                if not encounter.started_at:
                    encounter.started_at = timezone.now()
                encounter.save()
                from clinical.utils import log_patient_interaction
                log_patient_interaction(
                    patient = self.object,
                    action = "visit_created",
                    user = request.user,
                    description = f"Создан визит ID {encounter.id}",
                )
                messages.success(request, "Визит успешно создан.")
            else:
                messages.error(request, f"Ошибка в форме визита: {form.errors}")
            return redirect(self.request.path)

        # --- Добавить заметку ---
        if action == "add_note":
            if request.user.role not in {"ADMIN", "DOC", "NUR", "REG"}:
                messages.error(request, "Нет прав добавлять заметки.")
                return redirect(self.request.path)

            form = NoteForm(request.POST)
            form.fields["encounter"].queryset = Encounter.objects.filter(patient=self.object)

            if form.is_valid():
                note = form.save(commit=False)
                note.author = request.user
                note.save()
                from clinical.utils import log_patient_interaction
                log_patient_interaction(
                    patient = self.object,
                    action = "note_add",
                    user = request.user,
                    description = f"Добавлена заметка ID {note.id}",
                )
                messages.success(request, "Заметка добавлена.")
            else:
                messages.error(request, f"Ошибка заметки: {form.errors}")
            return redirect(self.request.path)

        # --- Добавить назначение ---
        if action == "add_rx":
            if request.user.role not in {"ADMIN", "DOC", "NUR"}:
                messages.error(request, "Нет прав добавлять назначения.")
                return redirect(self.request.path)

            form = PrescriptionForm(request.POST)
            form.fields["encounter"].queryset = Encounter.objects.filter(patient=self.object)

            if form.is_valid():
                rx = form.save(commit=False)
                rx.save()
                from clinical.utils import log_patient_interaction
                log_patient_interaction(
                    patient = self.object,
                    action = "rx_add",
                    user = request.user,
                    description = f"Добавлено назначение ID {rx.id}",
                )
                messages.success(request, "Назначение добавлено.")
            else:
                messages.error(request, f"Ошибка назначения: {form.errors}")
            return redirect(self.request.path)

        # --- Закрыть визит ---
        if action == "close_encounter":
            enc_id = request.POST.get("encounter_id")
            enc = get_object_or_404(Encounter, id=enc_id, patient=self.object)
            enc.finished_at = timezone.now()
            enc.status = Encounter.Status.FINISHED
            enc.save(update_fields=["finished_at", "status"])
            from clinical.utils import log_patient_interaction
            log_patient_interaction(
                patient = self.object,
                action = "visit_closed",
                user = request.user,
                description = f"Закрыт визит ID {enc_id}",
            )
            messages.success(request, "Визит закрыт.")
            return redirect(self.request.path)

        return redirect(self.request.path)

class PatientUpdate(RoleRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/update.html"
    allowed_roles = {"REG"}

    def get_success_url(self):
        return reverse("web:patient_detail", args=[self.object.id])
    def form_valid(self, form):
        old_facility = self.object.facility
        response = super().form_valid(form)
        # Логируем изменение места размещения, если оно изменилось
        log_patient_interaction(
            patient = self.object,
            action = "patient_update",
            user = self.request.user,
            description = f"Обновлена информация о пациенте ID {self.object.id}",
        )
        if old_facility != self.object.facility:
            old_name = old_facility.name if old_facility else "Без размещения"
            new_name = self.object.facility.name if self.object.facility else "Без размещения"
            log_patient_interaction(
                patient = self.object,
                action = "facility_update",
                user = self.request.user,
                description = f"Изменено место размещения с '{old_name}' на '{new_name}'",
            )
        return response

    


class AdultPatientList(PatientList):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(patient_type="adult")
class ChildrenPatients(PatientList):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(patient_type="child")

class PatientSoftDelete(RoleRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role != "REG":
            messages.error(request, "Нет прав удалять пациента.")
            return redirect("web:patients")
        patient = get_object_or_404(Patient, pk=pk)
        patient.is_active = False
        patient.save()
        messages.success(request, "Пациент успешно удален.")
        return redirect("web:patients")

class PatientRestore(RoleRequiredMixin, View):
    def post(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
        patient.is_active = True
        patient.save()
        messages.success(request, "Пациент восстановлен.")
        return redirect("web:patients")

class StatsView(RoleRequiredMixin, TemplateView):
    template_name = 'stats/departments.html'
    allowed_roles = {"ADMIN", "REG", "DOC", "NUR"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # 1. Получаем месяц из GET-параметров
        month_param = self.request.GET.get("month")  # формат YYYY-MM
        if month_param:
            year, month = map(int, month_param.split("-"))
        else:
            today = date.today()
            year, month = today.year, today.month

        # 2. Генерируем список всех дней месяца
        _, days_in_month = calendar.monthrange(year, month)
        dates = [str(day) for day in range(1, days_in_month + 1)]
        # 3. Фильтрация визитов по месяцу
        department = self.request.GET.get("department")
        encounters = Encounter.objects.filter(started_at__year=year, started_at__month=month)
        if department:
            encounters = encounters.filter(patient__department=department)

        # 4. Группировка: пациент + день
        data = encounters.values(
            "patient__last_name", "patient__first_name", "patient__document_id"
        ).annotate(
            day=TruncDay("started_at"),
            count=models.Count("id")
        )

        # 5. Уникальные пациенты
        patients = sorted({
            (row["patient__last_name"], row["patient__first_name"], row["patient__document_id"])
            for row in data
        })

        # 6. Таблица
        table = []
        for last, first, doc in patients:
            row = {"fio": f"{last} {first}", "document_id": doc, "visits": []}
            for d in dates:
                visit = next(
    (r["count"] for r in data
     if str(r["day"].day) == str(d) and
        r["patient__last_name"] == last and
        r["patient__first_name"] == first),
    0
)
                row["visits"].append(visit)
            table.append(row)

        ctx["dates"] = dates
        ctx["table"] = table
        ctx["departments"] = DEPARTMENT_CHOICES
        ctx["selected_month"] = f"{year}-{month:02d}"

        return ctx

class PatientCertificateView(RoleRequiredMixin, DetailView):
    model = Patient
    template_name = "patients/certificate.html"
    allowed_roles = {"ADMIN", "REG", "DOC"}

    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
        template_path = (
            settings.BASE_DIR
            / "templates"
            / "documents"
            / "certificate_template.docx"
        )
        if not os.path.exists(template_path):
            print("TEMPLATE PATH:", template_path)
            raise FileNotFoundError("Шаблон сертификата не найден.")
        doc = Document(template_path)
        content = {
            "{{FULL_NAME}}": f"{patient.last_name} {patient.first_name} {patient.middle_name or ''}".strip(),
            "{{DOCUMENT_ID}}": patient.document_id or "N/A",
            "{{ISSUE_DATE}}": now().strftime("%d.%m.%Y"),
        }
        for paragraph in doc.paragraphs:
            for key, value in content.items():
                if key in paragraph.text:
                    paragraph.text = paragraph.text.replace(key, value)
        filename = f"certificate_patient_{patient.id}.docx"
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        doc.save(response)
        return response



class Dashboard(RoleRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    allowed_roles = {"REG"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # --- Врачи ---
        doctors = (
            User.objects
            .filter(role="DOC", is_active=True)
            .annotate(
                total_patients=Count("patients", filter=Q(patients__is_active=True)),
                adult_patients=Count(
                    "patients",
                    filter=Q(patients__patient_type="adult", patients__is_active=True)
                ),
                child_patients=Count(
                    "patients",
                    filter=Q(patients__patient_type="child", patients__is_active=True)
                ),
                unknown_patients=Count(
                    "patients",
                    filter=Q(patients__patient_type="unknown", patients__is_active=True)
                ),
            )
            .order_by("last_name")
        )

        # --- KPI ---
        ctx["doctors_count"] = doctors.count()
        ctx["patients_total"] = Patient.objects.filter(is_active=True).count()
        ctx["patients_adult"] = Patient.objects.filter(patient_type="adult", is_active=True).count()
        ctx["patients_child"] = Patient.objects.filter(patient_type="child", is_active=True).count()
        ctx["patients_unknown"] = Patient.objects.filter(patient_type="unknown", is_active=True).count()

        ctx["doctors"] = doctors
        return ctx