from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import Doctor, Patient, Appointment, PregnancyVitals, Prescription, ModelMetric
from .serializers import (
    DoctorSerializer, PatientSerializer, AppointmentSerializer,
    PregnancyVitalsSerializer, VitalsPredictSerializer,
    PrescriptionSerializer, ModelMetricSerializer,
)
from .permissions import IsOwner


def calculate_risk(systolic_bp, diastolic_bp, blood_sugar, body_temp, heart_rate):
    """WHO eşiklerine göre maternal risk seviyesini hesaplar."""
    score = 0

    if systolic_bp > 140 or systolic_bp < 90:
        score += 2
    elif systolic_bp > 120:
        score += 1

    if diastolic_bp > 90 or diastolic_bp < 60:
        score += 2
    elif diastolic_bp > 80:
        score += 1

    if blood_sugar > 11 or blood_sugar < 3.5:
        score += 2
    elif blood_sugar > 7.5:
        score += 1

    if body_temp > 100.4 or body_temp < 97:
        score += 2
    elif body_temp > 99:
        score += 1

    if heart_rate > 100 or heart_rate < 60:
        score += 2
    elif heart_rate > 90:
        score += 1

    if score >= 5:
        return 'High'
    elif score >= 2:
        return 'Mid'
    return 'Low'


# API 1 & 2: Hasta CRUD (list, create, retrieve, update, destroy)
class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer

    def get_permissions(self):
        if self.action in ['list', 'create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwner]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'Admin':
            return Patient.objects.all().order_by('-id')
        return Patient.objects.filter(user=user).order_by('-id')

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'Admin':
            serializer.save()
        else:
            serializer.save(user=user)


# API 3 & 4: Gebelik vitalleri CRUD
class PregnancyVitalsViewSet(viewsets.ModelViewSet):
    serializer_class = PregnancyVitalsSerializer

    def get_permissions(self):
        if self.action in ['list', 'create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwner]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'Admin':
            return PregnancyVitals.objects.all().order_by('-recorded_at')
        return PregnancyVitals.objects.filter(patient__user=user).order_by('-recorded_at')


# API 5: Giriş yapan hastanın kendi ölçümleri
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_vitals(request):
    vitals = PregnancyVitals.objects.filter(patient__user=request.user).order_by('-recorded_at')
    serializer = PregnancyVitalsSerializer(vitals, many=True)
    return Response(serializer.data)


# API 6: Tüm doktorları listele
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_list(request):
    doctors = Doctor.objects.all()
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)


# API 7: Yeni doktor ekle
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_doctor(request):
    serializer = DoctorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API 8: Randevuları listele
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_list(request):
    user = request.user
    if hasattr(user, 'profile') and user.profile.role == 'Admin':
        appointments = Appointment.objects.all().order_by('-date')
    else:
        appointments = Appointment.objects.filter(patient__user=user).order_by('-date')
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)


# API 9: Yeni randevu oluştur
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_appointment(request):
    serializer = AppointmentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API 10: Vital ölçüm al ve risk tahmini yap
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vitals_predict(request):
    serializer = VitalsPredictSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        patient = Patient.objects.get(id=data['patient_id'])
    except Patient.DoesNotExist:
        return Response({'error': 'Hasta bulunamadı'}, status=status.HTTP_404_NOT_FOUND)

    risk_level = calculate_risk(
        data['systolic_bp'], data['diastolic_bp'],
        data['blood_sugar'], data['body_temp'], data['heart_rate'],
    )

    vitals = PregnancyVitals.objects.create(
        patient=patient,
        systolic_bp=data['systolic_bp'],
        diastolic_bp=data['diastolic_bp'],
        blood_sugar=data['blood_sugar'],
        body_temp=data['body_temp'],
        heart_rate=data['heart_rate'],
        risk_level=risk_level,
    )

    return Response({
        'tracking_code': str(vitals.tracking_code),
        'risk_level': vitals.risk_level,
        'recorded_at': vitals.recorded_at,
    }, status=status.HTTP_201_CREATED)


# API 11: TC kimlik numarasıyla sonuç sorgula (herkese açık)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_patient_result(request):
    full_name = request.data.get('full_name', '').strip().lower()
    national_id = request.data.get('national_id', '').strip()
    date_of_birth = request.data.get('date_of_birth')

    try:
        patient = Patient.objects.get(national_id=national_id)
    except Patient.DoesNotExist:
        return Response({'error': 'Kayıt bulunamadı'}, status=status.HTTP_404_NOT_FOUND)

    if patient.full_name.strip().lower() != full_name:
        return Response({'error': 'Bilgiler eşleşmiyor'}, status=status.HTTP_400_BAD_REQUEST)

    if date_of_birth and str(patient.date_of_birth) != str(date_of_birth):
        return Response({'error': 'Bilgiler eşleşmiyor'}, status=status.HTTP_400_BAD_REQUEST)

    latest = patient.vitals.order_by('-recorded_at').first()
    if not latest:
        return Response({'error': 'Henüz ölçüm kaydı yok'}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'patient_name': patient.full_name,
        'risk_level': latest.risk_level,
        'recorded_at': latest.recorded_at,
    })


# API 12: Yönetim paneli istatistikleri
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    stats = {
        'total_patients': Patient.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'total_vitals': PregnancyVitals.objects.count(),
        'model_metrics': ModelMetricSerializer(ModelMetric.objects.all(), many=True).data,
    }
    return Response(stats)


# API 13: Model doğruluk oranlarını listele
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_metrics_list(request):
    metrics = ModelMetric.objects.all()
    serializer = ModelMetricSerializer(metrics, many=True)
    return Response(serializer.data)


# API 14: Kullanıcı girişi, JWT token döndürür
@api_view(['POST'])
@permission_classes([AllowAny])
def custom_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        role = user.profile.role if hasattr(user, 'profile') else 'Visitor'
        patient_id = None
        if hasattr(user, 'patient_model'):
            patient_id = user.patient_model.id
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': role,
            'patient_id': patient_id,
            'name': user.get_full_name() or user.username,
        })
    return Response({'error': 'Geçersiz kullanıcı adı veya şifre'}, status=status.HTTP_401_UNAUTHORIZED)


# API 15: Giriş yapmış kullanıcının bilgileri
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    role = user.profile.role if hasattr(user, 'profile') else 'Visitor'
    return Response({
        'username': user.username,
        'email': user.email,
        'role': role,
        'full_name': user.get_full_name(),
    })
