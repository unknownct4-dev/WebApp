from django.urls import path  # path() maps a URL string to a view

from admindash import views  # Import all views from this app

# app_name enables URL namespacing so templates can use {% url 'admindash:index' %}
app_name = 'admindash'

urlpatterns = [
    # Main dashboard page — lists courses, enrollment requests, and admin accounts
    path('', views.DashboardView.as_view(), name='index'),

    # Add a new course (POST only)
    path('courses/add/', views.AddCourseView.as_view(), name='add_course'),

    # Remove a course by its primary key (POST only); blocked if the course has enrollment requests
    path('courses/<int:pk>/remove/', views.RemoveCourseView.as_view(), name='remove_course'),

    # Add a new subject to a course (POST only)
    path('subjects/add/', views.AddSubjectView.as_view(), name='add_subject'),

    # Remove a subject by its primary key (POST only)
    path('subjects/<int:pk>/remove/', views.RemoveSubjectView.as_view(), name='remove_subject'),

    # Set an enrollment request's status to 'verified' (POST only; only works if currently 'pending')
    path('enrollment/<int:pk>/verify/', views.VerifyEnrollmentView.as_view(), name='verify_enrollment'),

    # Set an enrollment request's status to 'rejected' (POST only; blocked if already 'rejected')
    path('enrollment/<int:pk>/reject/', views.RejectEnrollmentView.as_view(), name='reject_enrollment'),

    # Print verified student enrollment records sorted by course and year
    path('students/enrolled-records/print/', views.EnrolledRecordsPrintView.as_view(), name='print_enrolled_records'),

    # Approve a pending admin registration request and promote the user to admin (POST only)
    path('admin-requests/<int:pk>/approve/', views.ApproveAdminView.as_view(), name='approve_admin'),

    # Reject a pending admin registration request (POST only); user role stays 'student'
    path('admin-requests/<int:pk>/reject/', views.RejectAdminView.as_view(), name='reject_admin'),

    # Remove admin access from an active admin account, downgrading them to 'student' (POST only)
    path('admins/<int:pk>/revoke/', views.RevokeAdminView.as_view(), name='revoke_admin'),

    # Transfer the single super-admin role to another active admin (POST only)
    path('admins/<int:pk>/make-super-admin/', views.TransferSuperAdminView.as_view(), name='transfer_super_admin'),

    # Permanently delete a student account and all related records (POST only)
    path('students/<int:pk>/delete/', views.DeleteStudentView.as_view(), name='delete_student'),
]
