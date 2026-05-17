from django.urls import path  # path() maps a URL pattern to a view
from . import views           # Import all views from this app's views.py

# app_name enables URL namespacing so templates can use {% url 'landingpage:index' %}
app_name = 'landingpage'

urlpatterns = [
    # Root URL — renders the landing page with login and registration forms
    path('', views.IndexView.as_view(), name='index'),

    # Student-only login: authenticates via id_number + password (StudentBackend only)
    path('login/student/', views.StudentLoginView.as_view(), name='login_student'),

    # Admin-only login: authenticates via username + password (ModelBackend only)
    path('login/admin/', views.AdminLoginView.as_view(), name='login_admin'),

    # Handles logout (POST only); ends the session and redirects to the landing page
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Handles student registration form submission (POST only)
    path('register/student/', views.RegisterStudentView.as_view(), name='register_student'),

    # Handles admin registration request form submission (POST only)
    path('register/admin/', views.RegisterAdminView.as_view(), name='register_admin'),
]
