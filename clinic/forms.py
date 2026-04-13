from django import forms
from .models import Patient, Appointment, Doctor

BOOTSTRAP_INPUT = {'class': 'form-control'}
BOOTSTRAP_SELECT = {'class': 'form-select'}


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'national_id', 'date_of_birth', 'base_weight', 'phone_number']
        widgets = {
            'full_name': forms.TextInput(attrs={**BOOTSTRAP_INPUT, 'placeholder': 'Örn: Ayşe Kaya'}),
            'national_id': forms.TextInput(attrs={**BOOTSTRAP_INPUT, 'placeholder': '12345678901', 'maxlength': '11'}),
            'date_of_birth': forms.DateInput(attrs={**BOOTSTRAP_INPUT, 'type': 'date'}),
            'base_weight': forms.NumberInput(attrs={**BOOTSTRAP_INPUT, 'placeholder': 'Örn: 65.5', 'step': '0.1'}),
            'phone_number': forms.TextInput(attrs={**BOOTSTRAP_INPUT, 'placeholder': '+90 555 123 4567'}),
        }
        labels = {
            'full_name': 'Ad Soyad',
            'national_id': 'T.C. Kimlik No',
            'date_of_birth': 'Doğum Tarihi',
            'base_weight': 'Vücut Ağırlığı (kg)',
            'phone_number': 'Telefon Numarası',
        }


class VitalsForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        label='Hasta',
        empty_label='-- Hasta Seçin --',
        widget=forms.Select(attrs=BOOTSTRAP_SELECT),
    )
    systolic_bp = forms.FloatField(
        label='Sistolik Tansiyon (mmHg)',
        initial=120,
        widget=forms.NumberInput(attrs={**BOOTSTRAP_INPUT, 'step': '0.1', 'placeholder': 'Beklenen: 70-160'}),
    )
    diastolic_bp = forms.FloatField(
        label='Diastolik Tansiyon (mmHg)',
        initial=80,
        widget=forms.NumberInput(attrs={**BOOTSTRAP_INPUT, 'step': '0.1', 'placeholder': 'Beklenen: 40-100'}),
    )
    blood_sugar = forms.FloatField(
        label='Kan Şekeri (mmol/L)',
        initial=7.5,
        widget=forms.NumberInput(attrs={**BOOTSTRAP_INPUT, 'step': '0.1'}),
    )
    body_temp = forms.FloatField(
        label='Vücut Sıcaklığı (°F)',
        initial=98.6,
        widget=forms.NumberInput(attrs={**BOOTSTRAP_INPUT, 'step': '0.1'}),
    )
    heart_rate = forms.FloatField(
        label='Kalp Atış Hızı (bpm)',
        initial=75,
        widget=forms.NumberInput(attrs={**BOOTSTRAP_INPUT, 'step': '1'}),
    )


class ResultLookupForm(forms.Form):
    full_name = forms.CharField(
        label='Ad Soyad',
        widget=forms.TextInput(attrs={**BOOTSTRAP_INPUT, 'placeholder': 'Örn: Ayşe Kaya'}),
    )
    national_id = forms.CharField(
        label='T.C. Kimlik No (11 hane)',
        min_length=11,
        max_length=11,
        widget=forms.TextInput(attrs={**BOOTSTRAP_INPUT, 'placeholder': '12345678901'}),
    )
    date_of_birth = forms.DateField(
        label='Doğum Tarihi',
        widget=forms.DateInput(attrs={**BOOTSTRAP_INPUT, 'type': 'date'}),
    )


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'date', 'time', 'status']
        widgets = {
            'patient': forms.Select(attrs=BOOTSTRAP_SELECT),
            'doctor': forms.Select(attrs=BOOTSTRAP_SELECT),
            'date': forms.DateInput(attrs={**BOOTSTRAP_INPUT, 'type': 'date'}),
            'time': forms.TimeInput(attrs={**BOOTSTRAP_INPUT, 'type': 'time'}),
            'status': forms.Select(attrs=BOOTSTRAP_SELECT),
        }
        labels = {
            'patient': 'Hasta',
            'doctor': 'Doktor',
            'date': 'Tarih',
            'time': 'Saat',
            'status': 'Durum',
        }
