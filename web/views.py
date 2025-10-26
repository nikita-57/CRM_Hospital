# web/views.py
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.views.generic import UpdateView
from django.urls import reverse
from django.shortcuts import get_object_or_404
from .forms import PatientForm, EncounterForm, NoteForm, PrescriptionForm
from patients.models import Patient
from clinical.models import Encounter, Note, Prescription
from .mixins import RoleRequiredMixin, PatientFilterMixin


class Dashboard(RoleRequiredMixin, TemplateView):
    template_name = "dashboard.html"



class PatientList(RoleRequiredMixin, PatientFilterMixin, ListView):
    model = Patient
    template_name = "patients/list.html"
    paginate_by = 20
    allowed_roles = {"ADMIN", "REG", "DOC", "NUR"}

    def get_queryset(self):
        qs = super().get_queryset()

        qs = self.apply_filters(qs)
        user = self.request.user
        if user.role == "DOC":
            qs = qs.filter(department = user.department, is_active = True).distinct()

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(phone__icontains=q) |
                Q(document_id__icontains=q) |
                Q(insurance_number__icontains=q)
            )

        return qs



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
        # Фильтры для безопасности: врачи и медсёстры видят только своё отделение
        qs = super().get_queryset()
        user = self.request.user

        if user.role in {"DOC", "NUR"}:
            qs = qs.filter(department=user.department, is_active=True)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient: Patient = self.object

        # все визиты пациента
        enc_qs = Encounter.objects.filter(patient=patient).order_by("-started_at")
        ctx["encounters"] = enc_qs

        # форма создания визита
        ctx["encounter_form"] = EncounterForm(initial={
            "patient": patient.id,
            "doctor": self.request.user.id,
        })

        # формы заметок и назначений
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

        # --- создать визит ---
        if action == "add_encounter":
            if request.user.role not in {"ADMIN", "DOC", "NUR", "REG"}:
                messages.error(request, "Нет прав на создание визитов.")
                return redirect(self.request.path)

            form = EncounterForm(request.POST)
            if form.is_valid():
                encounter = form.save(commit=False)
                encounter.patient = self.object
                encounter.doctor = request.user
                if not encounter.started_at:
                    encounter.started_at = timezone.now()
                encounter.save()
                messages.success(request, "Визит успешно создан.")
            else:
                messages.error(request, "Ошибка в форме визита.")

            return redirect(self.request.path)

        # --- добавить заметку ---
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
                messages.success(request, "Заметка добавлена.")
            else:
                messages.error(request, "Ошибка при добавлении заметки.")

            return redirect(self.request.path)

        # --- добавить назначение ---
        if action == "add_rx":
            if request.user.role not in {"ADMIN", "DOC", "NUR"}:
                messages.error(request, "Нет прав добавлять назначения.")
                return redirect(self.request.path)

            form = PrescriptionForm(request.POST)
            form.fields["encounter"].queryset = Encounter.objects.filter(patient=self.object)

            if form.is_valid():
                rx = form.save(commit=False)
                rx.save()
                messages.success(request, "Назначение добавлено.")
            else:
                messages.error(request, "Ошибка при добавлении назначения.")

            return redirect(self.request.path)

        # --- закрыть визит ---
        if action == "close_encounter":
            enc_id = request.POST.get("encounter_id")
            enc = get_object_or_404(Encounter, id=enc_id, patient=self.object)
            enc.finished_at = timezone.now()
            enc.status = Encounter.Status.FINISHED
            enc.save(update_fields=["finished_at", "status"])
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
