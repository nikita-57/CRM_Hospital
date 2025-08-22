from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Prefetch
from .mixins import RoleRequiredMixin
from .forms import PatientForm, EncounterForm, NoteForm, PrescriptionForm
from patients.models import Patient
from clinical.models import Encounter, Note, Prescription
from django.db.models import Q

class Dashboard(RoleRequiredMixin, TemplateView):
    template_name = "dashboard.html"

class PatientList(RoleRequiredMixin, ListView):
    model = Patient
    template_name = "patients/list.html"
    paginate_by = 20
    allowed_roles = {"ADMIN","REG","DOC","NUR"}

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(phone__icontains=q) |
                Q(document_id__icontains=q) |      # ← поиск по личному номеру
                Q(insurance_number__icontains=q)    # (опционально) по полису
            )
        return qs

class PatientCreate(RoleRequiredMixin, CreateView):
    form_class = PatientForm
    template_name = "patients/create.html"
    success_url = reverse_lazy("web:patients")
    allowed_roles = {"ADMIN","REG"}

class PatientDetail(RoleRequiredMixin, DetailView):
    model = Patient
    template_name = "patients/detail.html"
    allowed_roles = {"ADMIN","REG","DOC","NUR"}

    def get_queryset(self):
        # Подтягиваем визиты/заметки/назначения заранее
        return (Patient.objects
            .prefetch_related(
                Prefetch("encounters", queryset=Encounter.objects.order_by("-started_at")
                         .prefetch_related("notes","prescriptions"))
            ))

    def post(self, request, *args, **kwargs):
        """Обрабатываем отправку инлайн-форм (заметка/назначение/визит) с одной страницы."""
        self.object = self.get_object()
        action = request.POST.get("action")

        if action == "add_encounter":
            if request.user.role not in {"ADMIN","DOC","NUR"}:
                messages.error(request, "Нет прав создавать визит.")
                return redirect(self.request.path)
            form = EncounterForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Визит создан.")
            else:
                messages.error(request, f"Ошибка: {form.errors}")
            return redirect(self.request.path)
            context = self.get_context_data()
            context["encounter_form"] = form
            context["open_madal"] = "encounter"
            return self.render_to_response(context)
        if action == "add_note":
            if request.user.role not in {"ADMIN","DOC","NUR"}:
                messages.error(request, "Нет прав добавлять заметки.")
                return redirect(self.request.path)
            form = NoteForm(request.POST)
            if form.is_valid():
                note: Note = form.save(commit=False)
                note.author = request.user
                note.save()
                messages.success(request, "Заметка добавлена.")
            else:
                messages.error(request, f"Ошибка: {form.errors}")
            return redirect(self.request.path)

        if action == "add_rx":
            if request.user.role not in {"ADMIN","DOC","NUR"}:
                messages.error(request, "Нет прав добавлять назначения.")
                return redirect(self.request.path)
            form = PrescriptionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Назначение добавлено.")
            else:
                messages.error(request, f"Ошибка: {form.errors}")
            return redirect(self.request.path)

        return redirect(self.request.path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient = self.object
        encounters = patient.encounters.all()
        ctx["encounters"] = encounters
        # Формы по умолчанию подставляют пациента/врача/визит
        ctx["encounter_form"] = EncounterForm(initial={"patient": patient.id, "doctor": self.request.user.id})
        # Если есть хоть один визит — будем привязывать к нему по умолчанию
        default_enc = encounters[0].id if encounters else None
        ctx["note_form"] = NoteForm(initial={"encounter": default_enc})
        ctx["rx_form"] = PrescriptionForm(initial={"encounter": default_enc})
        return ctx
