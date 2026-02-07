from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0010_patient_employer"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="callsign",
            field=models.CharField(blank=True, max_length=64, verbose_name="Позывной"),
        ),
    ]
