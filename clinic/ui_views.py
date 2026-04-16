from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Patient, Doctor, Appointment, PregnancyVitals, ModelMetric
from .forms import (
    PatientForm, VitalsForm, ResultLookupForm,
    AppointmentForm, PatientAppointmentForm,
    DoctorForm, PatientRegisterForm,
)
from .views import calculate_risk


def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'Admin'


def login_view(request):
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('dashboard')
        return redirect('vitals_list')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if is_admin(user):
                return redirect('dashboard')
            return redirect('vitals_list')
        messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
    return render(request, 'clinic/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('vitals_list')
    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data['national_id'],
                password=data['password'],
            )
            patient = Patient.objects.create(
                user=user,
                full_name=data['full_name'],
                national_id=data['national_id'],
                date_of_birth=data['date_of_birth'],
                base_weight=data['base_weight'],
                phone_number=data['phone_number'],
            )
            # Sinyal profil oluşturdu, hasta kaydını bağla
            user.profile.patient_record = patient
            user.profile.save()
            login(request, user)
            messages.success(request, 'Hesabınız oluşturuldu. Hoş geldiniz!')
            return redirect('vitals_list')
    else:
        form = PatientRegisterForm()
    return render(request, 'clinic/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    # Hasta kullanıcılar dashboard'a erişemez
    if not is_admin(request.user):
        return redirect('vitals_list')
    context = {
        'total_patients': Patient.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'total_vitals': PregnancyVitals.objects.count(),
        'metrics': ModelMetric.objects.all(),
        'recent_vitals': PregnancyVitals.objects.select_related('patient').order_by('-recorded_at')[:5],
    }
    return render(request, 'clinic/dashboard.html', context)


@login_required
def patient_list_view(request):
    search = request.GET.get('search', '')
    patients = Patient.objects.all().order_by('full_name')
    if search:
        patients = patients.filter(full_name__icontains=search) | \
                   patients.filter(national_id__icontains=search) | \
                   patients.filter(phone_number__icontains=search)
    return render(request, 'clinic/patient_list.html', {
        'patients': patients,
        'search': search,
    })


@login_required
def patient_create_view(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hasta başarıyla kaydedildi.')
            return redirect('patient_list')
    else:
        form = PatientForm()
    return render(request, 'clinic/patient_form.html', {'form': form})


@login_required
def vitals_list_view(request):
    user = request.user
    if is_admin(user):
        vitals = PregnancyVitals.objects.all().select_related('patient').order_by('-recorded_at')
    else:
        vitals = PregnancyVitals.objects.filter(patient__user=user).order_by('-recorded_at')
    return render(request, 'clinic/vitals_list.html', {'vitals': vitals})


@login_required
def vitals_predict_view(request):
    patient_id = request.GET.get('patient')
    initial = {}
    if patient_id:
        initial['patient'] = patient_id

    if request.method == 'POST':
        form = VitalsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            patient = data['patient']
            risk_level = calculate_risk(
                data['systolic_bp'], data['diastolic_bp'],
                data['blood_sugar'], data['body_temp'], data['heart_rate'],
            )
            PregnancyVitals.objects.create(
                patient=patient,
                systolic_bp=data['systolic_bp'],
                diastolic_bp=data['diastolic_bp'],
                blood_sugar=data['blood_sugar'],
                body_temp=data['body_temp'],
                heart_rate=data['heart_rate'],
                risk_level=risk_level,
            )
            risk_labels = {'Low': 'Düşük', 'Mid': 'Orta', 'High': 'Yüksek'}
            messages.success(request, f'Ölçüm kaydedildi. Risk Seviyesi: {risk_labels.get(risk_level, risk_level)}')
            return redirect('vitals_list')
    else:
        form = VitalsForm(initial=initial)
    return render(request, 'clinic/vitals_form.html', {'form': form})


def result_lookup_view(request):
    # Giriş yapmış hasta kendi tüm sonuçlarını görür
    if request.user.is_authenticated and not is_admin(request.user):
        try:
            patient = request.user.patient_model
            vitals = patient.vitals.order_by('-recorded_at')
        except Exception:
            vitals = []
        return render(request, 'clinic/result_lookup.html', {'patient_vitals': vitals})

    # Giriş yapılmamış ziyaretçi için TC ile sorgulama formu
    result = None
    error = None
    if request.method == 'POST':
        form = ResultLookupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                patient = Patient.objects.get(national_id=data['national_id'])
                name_match = patient.full_name.strip().lower() == data['full_name'].strip().lower()
                dob_match = patient.date_of_birth == data['date_of_birth']
                if name_match and dob_match:
                    latest = patient.vitals.order_by('-recorded_at').first()
                    if latest:
                        result = {
                            'patient_name': patient.full_name,
                            'risk_level': latest.risk_level,
                            'recorded_at': latest.recorded_at,
                        }
                    else:
                        error = 'Henüz kayıtlı bir ölçüm bulunamadı.'
                else:
                    error = 'Girilen bilgiler kayıtlarla eşleşmiyor.'
            except Patient.DoesNotExist:
                error = 'Bu kimlik numarasına ait kayıt bulunamadı.'
    else:
        form = ResultLookupForm()
    return render(request, 'clinic/result_lookup.html', {
        'form': form,
        'result': result,
        'error': error,
    })


@login_required
def doctor_list_view(request):
    doctors = Doctor.objects.all().order_by('name')
    return render(request, 'clinic/doctor_list.html', {'doctors': doctors})


@login_required
def doctor_create_view(request):
    if not is_admin(request.user):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('doctor_list')
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doktor başarıyla eklendi.')
            return redirect('doctor_list')
    else:
        form = DoctorForm()
    return render(request, 'clinic/doctor_form.html', {'form': form})


@login_required
def appointment_list_view(request):
    user = request.user
    if is_admin(user):
        appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-date')
    else:
        appointments = Appointment.objects.filter(patient__user=user).select_related('doctor').order_by('-date')
    return render(request, 'clinic/appointment_list.html', {'appointments': appointments})


@login_required
def appointment_create_view(request):
    user = request.user
    admin = is_admin(user)

    if request.method == 'POST':
        if admin:
            form = AppointmentForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Randevu başarıyla oluşturuldu.')
                return redirect('appointment_list')
        else:
            form = PatientAppointmentForm(request.POST)
            if form.is_valid():
                try:
                    patient = user.patient_model
                except Exception:
                    messages.error(request, 'Hasta kaydınız bulunamadı.')
                    return redirect('appointment_list')
                Appointment.objects.create(
                    patient=patient,
                    doctor=form.cleaned_data['doctor'],
                    date=form.cleaned_data['date'],
                    time=form.cleaned_data['time'],
                    status='Scheduled',
                )
                messages.success(request, 'Randevunuz başarıyla oluşturuldu.')
                return redirect('appointment_list')
    else:
        form = AppointmentForm() if admin else PatientAppointmentForm()

    return render(request, 'clinic/appointment_form.html', {'form': form, 'is_admin': admin})
