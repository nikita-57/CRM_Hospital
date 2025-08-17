# clinical/urls.py
from rest_framework.routers import DefaultRouter
from .views import EncounterViewSet, NoteViewSet, DiagnosisViewSet, PrescriptionViewSet, AttachmentViewSet
router = DefaultRouter()
router.register(r"encounters", EncounterViewSet)
router.register(r"notes", NoteViewSet)
router.register(r"diagnoses", DiagnosisViewSet)
router.register(r"prescriptions", PrescriptionViewSet)
router.register(r"attachments", AttachmentViewSet)
urlpatterns = router.urls
