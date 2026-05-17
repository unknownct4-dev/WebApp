from django.urls import path  # path() maps a URL string to a view
from . import views           # Import all views from this app

# app_name enables URL namespacing so templates can use {% url 'studenthome:index' %}
app_name = 'studenthome'

urlpatterns = [
    # Student home page — renders the four-tab layout (GET only)
    path('', views.HomeView.as_view(), name='index'),

    # Enrollment submission endpoint — accepts POST from the Enrollment tab (AJAX)
    path('enroll/', views.EnrollView.as_view(), name='enroll'),
]
