from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from planning.models import Event, DEPARTMENT_CHOICES
from web.forms import EventForm
from web.mixins import RoleRequiredMixin
from accounts.models import User


class PlanningView(RoleRequiredMixin, TemplateView):
    """Окно планирования мероприятий."""
    template_name = "planning/list.html"
    allowed_roles = {"ADMIN", "REG", "DOC", "LEAD", "NUR"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Фильтры
        department = self.request.GET.get("department")
        event_type = self.request.GET.get("event_type")
        is_completed = self.request.GET.get("is_completed")
        responsible = self.request.GET.get("responsible")

        # Базовый queryset с учётом прав доступа
        events = Event.objects.all().select_related("responsible", "created_by")

        # Ограничение просмотра по ролям
        if user.role == "ADMIN":
            # Админ видит всё
            pass
        elif user.role in {"LEAD", "DOC", "NUR"}:
            # LEAD, DOC и NUR видят только своё отделение
            events = events.filter(department=user.department)
        elif user.role == "REG":
            # Регистратор видит общие мероприятия (без отделения) и созданные им
            events = events.filter(Q(department="") | Q(created_by=user))

        # Применяем фильтры
        # LEAD, DOC, NUR не могут фильтровать по отделению (только своё)
        if department and user.role in {"ADMIN", "REG"}:
            events = events.filter(department=department)
        if event_type:
            events = events.filter(event_type=event_type)
        if is_completed is not None:
            events = events.filter(is_completed=is_completed == "true")
        else:
            # По умолчанию показываем только невыполненные
            events = events.filter(is_completed=False)
        
        # Фильтр по исполнителю
        if responsible:
            try:
                executor = User.objects.get(id=responsible)
                if executor.role == "LEAD":
                    # Если выбран LEAD, показываем все мероприятия его отделения
                    events = events.filter(department=executor.department)
                else:
                    # Если выбран DOC/NUR, показываем мероприятия где он ответственный
                    events = events.filter(responsible_id=responsible)
            except User.DoesNotExist:
                pass

        ctx["events"] = events
        ctx["departments"] = DEPARTMENT_CHOICES
        ctx["event_types"] = Event.EVENT_TYPES
        ctx["selected_department"] = department or ""
        ctx["selected_event_type"] = event_type or ""
        
        # Список исполнителей для фильтра
        if user.role in {"ADMIN", "REG", "LEAD"}:
            if user.role == "LEAD":
                # LEAD видит себя и сотрудников своего отделения
                executors = User.objects.filter(
                    role__in={"DOC", "NUR", "LEAD"},
                    department=user.department,
                    is_active=True
                ).order_by("last_name", "first_name")
            elif user.role == "REG":
                # REG видит всех LEAD и врачей/медсестёр по отделениям
                # Группируем: сначала LEAD, потом DOC/NUR
                leads = User.objects.filter(role="LEAD", is_active=True).order_by("department", "last_name", "first_name")
                staff = User.objects.filter(
                    role__in={"DOC", "NUR"},
                    is_active=True
                ).order_by("department", "last_name", "first_name")
                # Объединяем queryset'ы
                executors = list(leads) + list(staff)
            else:
                # ADMIN видит всех
                executors = User.objects.filter(
                    role__in={"DOC", "NUR", "LEAD"},
                    is_active=True
                ).order_by("last_name", "first_name")
            ctx["executors"] = executors
        elif user.role in {"DOC", "NUR"}:
            # DOC и NUR видят коллег своего отделения
            ctx["executors"] = User.objects.filter(
                role__in={"DOC", "NUR", "LEAD"},
                department=user.department,
                is_active=True
            ).order_by("last_name", "first_name")
        else:
            ctx["executors"] = User.objects.none()
        
        ctx["selected_responsible"] = responsible or ""

        # Права для отображения кнопок
        ctx["can_create"] = user.role in {"ADMIN", "REG", "LEAD", "DOC", "NUR"}
        ctx["can_delete"] = user.role in {"ADMIN", "REG", "LEAD"}
        ctx["can_toggle"] = user.role in {"ADMIN", "REG", "LEAD", "DOC", "NUR"}

        # Форма для нового мероприятия
        ctx["event_form"] = EventForm()

        return ctx

    def post(self, request, *args, **kwargs):
        """Обработка создания нового мероприятия."""
        action = request.POST.get("action")
        user = request.user

        if action == "add_event":
            if user.role not in {"ADMIN", "REG", "LEAD", "DOC", "NUR"}:
                messages.error(request, "Нет прав на создание мероприятий.")
                return redirect("planning:list")

            form = EventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.created_by = user

                # LEAD, DOC и NUR всегда получают своё отделение
                if user.role in {"LEAD", "DOC", "NUR"}:
                    event.department = user.department

                event.save()
                messages.success(request, "Мероприятие успешно создано.")
            else:
                messages.error(request, f"Ошибка в форме: {form.errors}")
            return redirect("planning:list")

        if action == "toggle_event":
            event_id = request.POST.get("event_id")
            event = get_object_or_404(Event, id=event_id)
            
            # Проверка прав на изменение статуса
            if user.role not in {"ADMIN", "REG", "LEAD", "DOC"}:
                messages.error(request, "Нет прав на изменение статуса мероприятия.")
                return redirect("planning:list")
            
            # DOC и NUR могут менять только мероприятия своего отделения
            if user.role in {"DOC", "NUR"} and event.department != user.department:
                messages.error(request, "Можно менять только мероприятия своего отделения.")
                return redirect("planning:list")
            
            event.is_completed = not event.is_completed
            event.save(update_fields=["is_completed"])
            messages.success(request, "Статус мероприятия обновлён.")
            return redirect("planning:list")

        if action == "delete_event":
            event_id = request.POST.get("event_id")
            event = get_object_or_404(Event, id=event_id)
            
            if user.role not in {"ADMIN", "REG", "LEAD"}:
                messages.error(request, "Нет прав на удаление мероприятия.")
                return redirect("planning:list")
            
            # LEAD и REG могут удалять только свои мероприятия
            if user.role in {"LEAD", "REG"} and event.created_by != user:
                messages.error(request, "Можно удалять только созданные вами мероприятия.")
                return redirect("planning:list")
            
            event.delete()
            messages.success(request, "Мероприятие удалено.")
            return redirect("planning:list")

        return redirect("planning:list")
