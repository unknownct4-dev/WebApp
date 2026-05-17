from django.urls import path  # path() maps a URL string to a view
from . import views           # Import all views from this app

# app_name enables URL namespacing so templates can use {% url 'studentenrollment:index' %}
app_name = 'studentenrollment'

urlpatterns = [
    # Main enrollment form page (GET renders the form; POST submits it)
    path('', views.EnrollmentView.as_view(), name='index'),

    # JSON endpoint that returns subjects for a given course code or ID
    # Used by the enrollment form's JavaScript to dynamically populate the subject list
    path('subjects/<str:course_code>/', views.SubjectsJsonView.as_view(), name='subjects_json'),

    # Confirmation page shown after a successful enrollment submission
    path('confirmation/', views.ConfirmationView.as_view(), name='confirmation'),
]
