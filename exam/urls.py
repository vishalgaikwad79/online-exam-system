from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.student_register, name='register'),
    path('login/', views.student_login, name='login'),
    path('logout/', views.student_logout, name='logout'),
    path('index/', views.index, name='index'),
    path('subjects/', views.subject_list, name='subjects'),
    path('exam/<int:subject_id>/', views.start_exam, name='start_exam'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('ranking/', views.ranking, name='ranking'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('profile/', views.profile, name='profile'),
    path('reset-password/', views.reset_password, name='reset_password'),
]