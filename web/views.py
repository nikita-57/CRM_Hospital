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


# web/views.py
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
            qs = qs.filter(encounters__doctor=user).distinct()

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

    # заранее подтягиваем связанные объекты
    def get_queryset(self):
        return (
            Patient.objects
            .prefetch_related(
                Prefetch(
                    "encounters",
                    queryset=Encounter.objects.order_by("-started_at")
                        .prefetch_related("notes", "prescriptions", "attachments")
                )
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient: Patient = self.object

        # только визиты текущего пациента
        enc_qs = Encounter.objects.filter(patient=patient).order_by("started_at")
        ctx["encounters"] = enc_qs

        # --- форма визита (для модалки) ---
        # фиксируем пациента и текущего пользователя-врача (поля будут скрыты в форме)
        ctx.setdefault("encounter_form", EncounterForm(initial={
            "patient": patient.id,
            "doctor": self.request.user.id,
        }))

        # --- формы заметки и назначения ---
        default_enc_id = enc_qs[0].id if enc_qs else None

        note_form = ctx.get("note_form") or NoteForm(initial={"encounter": default_enc_id})
        note_form.fields["encounter"].queryset = enc_qs
        ctx["note_form"] = note_form

        rx_form = ctx.get("rx_form") or PrescriptionForm(initial={"encounter": default_enc_id})
        rx_form.fields["encounter"].queryset = enc_qs
        ctx["rx_form"] = rx_form

        return ctx

    def post(self, request, *args, **kwargs):
        self.object: Patient = self.get_object()
        action = request.POST.get("action")

        # --- создать визит (модалка) ---
        if action == "add_encounter":
            if request.user.role not in {"ADMIN", "DOC", "NUR"}:
                messages.error(request, "Нет прав создавать визит.")
                return redirect(self.request.path)

            form = EncounterForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Визит создан.")
                return redirect(self.request.path)

            # невалидная форма — показываем модалку снова
            context = self.get_context_data()
            context["encounter_form"] = form
            context["open_modal"] = "encounter"
            return self.render_to_response(context)

        # --- добавить заметку ---
        if action == "add_note":
            if request.user.role not in {"ADMIN", "DOC", "NUR"}:
                messages.error(request, "Нет прав добавлять заметки.")
                return redirect(self.request.path)

            form = NoteForm(request.POST)
            # ограничим выбор визитов этим пациентом
            form.fields["encounter"].queryset = Encounter.objects.filter(patient=self.object)

            if form.is_valid():
                note: Note = form.save(commit=False)
                note.author = request.user
                # безопасность: убеждаемся, что заметка к визиту этого пациента
                if note.encounter.patient_id != self.object.id:
                    messages.error(request, "Нельзя добавить заметку к другому пациенту.")
                    return redirect(self.request.path)
                note.save()
                messages.success(request, "Заметка добавлена.")
            else:
                messages.error(request, "Проверьте поля заметки.")
            return redirect(self.request.path)

        # --- добавить назначение ---
        if action == "add_rx":
            if request.user.role not in {"ADMIN", "DOC", "NUR"}:
                messages.error(request, "Нет прав добавлять назначения.")
                return redirect(self.request.path)

            form = PrescriptionForm(request.POST)
            form.fields["encounter"].queryset = Encounter.objects.filter(patient=self.object)

            if form.is_valid():
                rx: Prescription = form.save(commit=False)
                if rx.encounter.patient_id != self.object.id:
                    messages.error(request, "Нельзя добавить назначение к другому пациенту.")
                    return redirect(self.request.path)
                rx.save()
                messages.success(request, "Назначение добавлено.")
            else:
                messages.error(request, "Проверьте поля назначения.")
            return redirect(self.request.path)

        # --- закрыть визит ---
        if action == "close_encounter":
            if request.user.role not in {"ADMIN", "DOC", "NUR"}:
                messages.error(request, "Нет прав закрывать визит.")
                return redirect(self.request.path)

            enc_id = request.POST.get("encounter_id")
            try:
                enc = self.object.encounters.get(id=enc_id)
            except Encounter.DoesNotExist:
                messages.error(request, "Визит не найден.")
                return redirect(self.request.path)

            enc.finished_at = timezone.now()
            enc.status = Encounter.Status.FINISHED
            enc.save(update_fields=["finished_at", "status"])
            messages.success(request, "Визит закрыт.")
            return redirect(self.request.path)

        # неизвестное действие
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
