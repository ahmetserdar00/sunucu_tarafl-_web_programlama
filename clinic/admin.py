from django.contrib import admin
from .models import Doctor, Patient, Appointment, PregnancyVitals, Prescription, ModelMetric, UserProfile


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialty', 'phone_number']
    search_fields = ['name', 'specialty']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'national_id', 'age', 'base_weight', 'phone_number']
    search_fields = ['full_name', 'national_id', 'phone_number']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'time', 'status']
    list_filter = ['status', 'date']


@admin.register(PregnancyVitals)
class PregnancyVitalsAdmin(admin.ModelAdmin):
    list_display = ['patient', 'risk_level', 'systolic_bp', 'diastolic_bp', 'blood_sugar', 'recorded_at']
    list_filter = ['risk_level']
    readonly_fields = ['tracking_code', 'recorded_at']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date_issued']


@admin.register(ModelMetric)
class ModelMetricAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'accuracy_score']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'patient_record']
    list_filter = ['role']
