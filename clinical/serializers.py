from rest_framework import serializers
from .models import Encounter, Note, Diagnosis, Prescription, Attachment

class NoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    class Meta:
        model = Note
        fields = ["id","author","author_name","created_at","text","encounter"]
        read_only_fields = ["author","created_at"]

class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = "__all__"

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = "__all__"

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"

class EncounterSerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True, read_only=True)
    diagnoses = DiagnosisSerializer(many=True, read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = Encounter
        fields = ["id","patient","doctor","started_at","finished_at","reason","status",
                  "notes","diagnoses","prescriptions"]