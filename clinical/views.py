from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Encounter, Note, Diagnosis, Prescription, Attachment
from .serializers import EncounterSerializer, NoteSerializer, DiagnosisSerializer, PrescriptionSerializer, AttachmentSerializer

class IsDoctorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role in {"ADMIN","DOC","NUR"}

class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.select_related("patient","doctor").all()
    serializer_class = EncounterSerializer
    permission_classes = [IsDoctorOrReadOnly]

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsDoctorOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsDoctorOrReadOnly]

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctorOrReadOnly]

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsDoctorOrReadOnly]