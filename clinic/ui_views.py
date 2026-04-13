from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Patient, Doctor, Appointment, PregnancyVitals, ModelMetric
from .forms import PatientForm, VitalsForm, ResultLookupForm, AppointmentForm
from .views import calculate_risk


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
    return render(request, 'clinic/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
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
    if hasattr(user, 'profile') and user.profile.role == 'Admin':
        vitals = PregnancyVitals.objects.all().select_related('patient').order_by('-recorded_at')
    else:
        vitals = PregnancyVitals.objects.filter(patient__user=user).order_by('-recorded_at')
    return render(request, 'clinic/vitals_list.html', {'vitals': vitals})


@login_required
def vitals_predict_view(request):
    # Hasta listesinden "Ölçüm Al" butonuyla gelindiyse hastayı ön seçili yap
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
def appointment_list_view(request):
    user = request.user
    if hasattr(user, 'profile') and user.profile.role == 'Admin':
        appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-date')
    else:
        appointments = Appointment.objects.filter(patient__user=user).select_related('doctor').order_by('-date')
    return render(request, 'clinic/appointment_list.html', {'appointments': appointments})


@login_required
def appointment_create_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Randevu başarıyla oluşturuldu.')
            return redirect('appointment_list')
    else:
        form = AppointmentForm()
    return render(request, 'clinic/appointment_form.html', {'form': form})
