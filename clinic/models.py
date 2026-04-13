import uuid
from datetime import date
from django.db import models
from django.conf import settings


class Doctor(models.Model):
    name = models.CharField(max_length=255)
    specialty = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"Dr. {self.name} - {self.specialty}"


class Patient(models.Model):
    # Kullanıcı hesabıyla bağlantılı, olmayabilir (admin tarafından eklenen hastalar için)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='patient_model'
    )
    full_name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=11, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    base_weight = models.FloatField(help_text="Vücut ağırlığı (kg)")
    phone_number = models.CharField(max_length=20)

    @property
    def age(self):
        if not self.date_of_birth:
            return 0
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def __str__(self):
        return str(self.full_name)


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Planlandı'),
        ('Completed', 'Tamamlandı'),
        ('Cancelled', 'İptal Edildi'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Scheduled')

    def __str__(self):
        return f"{self.patient.full_name} - Dr. {self.doctor.name} ({self.date})"


class PregnancyVitals(models.Model):
    RISK_LEVEL_CHOICES = [
        ('Low', 'Düşük'),
        ('Mid', 'Orta'),
        ('High', 'Yüksek'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    systolic_bp = models.FloatField(help_text="Sistolik tansiyon (mmHg)")
    diastolic_bp = models.FloatField(help_text="Diastolik tansiyon (mmHg)")
    blood_sugar = models.FloatField(help_text="Kan şekeri (mmol/L)")
    body_temp = models.FloatField(help_text="Vücut sıcaklığı (°F)")
    heart_rate = models.FloatField(help_text="Kalp atış hızı (bpm)")
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.full_name} | Risk: {self.risk_level}"


class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    medication_details = models.TextField()
    date_issued = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Reçete: {self.patient.full_name} - Dr. {self.doctor.name}"


class ModelMetric(models.Model):
    # Makine öğrenmesi algoritmalarının doğruluk oranlarını tutar
    model_name = models.CharField(max_length=255)
    accuracy_score = models.FloatField()

    def __str__(self):
        return f"{self.model_name}: %{self.accuracy_score}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Patient', 'Hasta'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Patient')
    patient_record = models.OneToOneField(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"
