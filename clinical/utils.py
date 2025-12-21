from clinical.models import PatientInteraction
def log_patient_interaction(*, patient, action, user, description=""):
    """Логирует взаимодействие с пациентом."""
    PatientInteraction.objects.create(
        patient = patient,
        action = action,
        user = user,
        description = description,
    )
    