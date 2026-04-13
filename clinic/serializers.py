from rest_framework import serializers
from .models import Doctor, Patient, Appointment, PregnancyVitals, Prescription, ModelMetric


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()

    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'national_id', 'date_of_birth', 'base_weight', 'phone_number', 'age']


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'


class PregnancyVitalsSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    tracking_code = serializers.UUIDField(read_only=True)

    class Meta:
        model = PregnancyVitals
        fields = '__all__'
        read_only_fields = ['risk_level', 'recorded_at', 'tracking_code']


class VitalsPredictSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    systolic_bp = serializers.FloatField()
    diastolic_bp = serializers.FloatField()
    blood_sugar = serializers.FloatField()
    body_temp = serializers.FloatField()
    heart_rate = serializers.FloatField()


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'


class ModelMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelMetric
        fields = '__all__'
