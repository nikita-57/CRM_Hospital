from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Patient
from .serializers import PatientSerializer

class IsRegistrarOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role in {"ADMIN","REG"}

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsRegistrarOrReadOnly]
