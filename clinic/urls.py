from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, ui_views

router = DefaultRouter()
router.register('patients', views.PatientViewSet, basename='patient')
router.register('vitals-data', views.PregnancyVitalsViewSet, basename='vitals-data')

urlpatterns = [
    # Şablon tabanlı arayüz sayfaları
    path('', ui_views.login_view, name='login'),
    path('logout/', ui_views.logout_view, name='logout'),
    path('dashboard/', ui_views.dashboard_view, name='dashboard'),
    path('patients/', ui_views.patient_list_view, name='patient_list'),
    path('patients/new/', ui_views.patient_create_view, name='patient_create'),
    path('vitals/', ui_views.vitals_list_view, name='vitals_list'),
    path('vitals/predict/', ui_views.vitals_predict_view, name='vitals_predict'),
    path('result-lookup/', ui_views.result_lookup_view, name='result_lookup'),
    path('doctors/', ui_views.doctor_list_view, name='doctor_list'),
    path('doctors/new/', ui_views.doctor_create_view, name='doctor_create'),
    path('appointments/', ui_views.appointment_list_view, name='appointment_list'),
    path('appointments/new/', ui_views.appointment_create_view, name='appointment_create'),

    # REST API endpointleri
    path('api/', include(router.urls)),
    path('api/my-vitals/', views.my_vitals, name='my_vitals'),
    path('api/doctors/', views.doctor_list, name='doctor_list_api'),
    path('api/doctors/create/', views.create_doctor, name='create_doctor_api'),
    path('api/appointments/', views.appointment_list, name='appointment_list_api'),
    path('api/appointments/create/', views.create_appointment, name='create_appointment'),
    path('api/vitals/predict/', views.create_vitals_predict, name='create_vitals_predict'),
    path('api/verify-result/', views.verify_patient_result, name='verify_patient_result'),
    path('api/dashboard/', views.dashboard_stats, name='dashboard_stats'),
    path('api/model-metrics/', views.model_metrics_list, name='model_metrics_list'),
    path('api/auth/login/', views.custom_login, name='login_api'),
    path('api/auth/me/', views.me, name='me'),
]
