from django.urls import path  # path() maps a URL string to a view

from studentprofile import views  # Import all views from this app

# app_name enables URL namespacing so templates can use {% url 'studentprofile:index' %}
app_name = 'studentprofile'

urlpatterns = [
    # Student profile page — displays user info and enrolled subjects (GET only)
    path('', views.ProfileView.as_view(), name='index'),

    # Profile edit form — GET renders the pre-filled form; POST saves changes
    path('edit/', views.EditProfileView.as_view(), name='edit'),

    # Profile photo upload endpoint — POST only; saves the photo and updates the user record
    path('photo/', views.UploadPhotoView.as_view(), name='upload_photo'),
]
